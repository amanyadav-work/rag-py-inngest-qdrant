import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from inngest.experimental import ai
from dotenv import load_dotenv
import uuid
import os
import datetime
from data_loader import load_and_chunk_pdf, emded_texts
from vector_db import QdrantStorage
from custom_types import RAGChunkAndSrc, RAGQueryResult, RAGSearchResult, RAGUpsertResult, IngestRequest, QueryRequest
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

load_dotenv()

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=True,
    serializer=inngest.PydanticSerializer()
)

app = FastAPI()

@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf")
)
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, source_id=source_id)
    
    def _upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.source_id
        vecs = emded_texts(chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}: {i}")) for i in range(len(chunks))]
        payloads = [{"source": source_id, "text": chunks[i]} for i in range(len(chunks))]
        collection = ctx.event.data.get("collection","docs")
        QdrantStorage(collection=collection).upsert(ids, vecs, payloads)
        return RAGUpsertResult(ingested=len(chunks))
    
    chunks_and_src = await ctx.step.run(step_id="load-and-chunk", handler= lambda: _load(ctx), output_type=RAGChunkAndSrc)
    
    ingested = await ctx.step.run(step_id="embed-and-upsert", handler= lambda: _upsert(chunks_and_src), output_type=RAGUpsertResult)
    
    return ingested.model_dump()


@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/query_pdf_ai")
)
async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> RAGSearchResult:
        query_vec = emded_texts([question])[0]
        collection = ctx.event.data.get("collection","docs")
        store = QdrantStorage(collection=collection)
        found = store.search(query_vec, top_k)
        return RAGSearchResult(contexts=found["contexts"], sources=found["sources"])
    
    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))
    
    found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k), output_type=RAGSearchResult)
    
    context_block = "\n\n".join(f"- {c}" for c in found.contexts)
    
    user_content = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )
    
    response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant that answers questions based on the provided context."),
            contents=user_content
    )
    
    print(found)
    answer = response.text
    return {
        "answer": answer,
        "sources": found.sources,
        "num_contexts": len(found.contexts)
    }


# Route endpoints can perform actions.. but can't return fn responses coz limitations in .send method - it only returns ids not full response.. i'll see more about this in custom webservices later

# Ingestion route (PATCH)
@app.patch("/ingest-pdf")
async def ingest_pdf(request: IngestRequest):
    collection = request.collection  # Take collection from request
    pdf_path = request.pdf_path
    source_id = request.source_id or pdf_path  # Default source_id to pdf_path if not provided

    try:
        trigger_event = inngest.Event(
        name="rag/ingest_pdf",  # Event name
        data={
        "pdf_path": pdf_path,
        "source_id": source_id,
        "collection": collection
        }
        )
        response = inngest_client.send_sync(trigger_event)
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting PDF: {str(e)}")

# Query route (POST)
@app.post("/query-pdf-ai")
async def query_pdf_ai(request: QueryRequest):
    collection = request.collection  # Take collection from request
    question = request.question
    top_k = request.top_k

    try:
        trigger_event = inngest.Event(
        name="rag/query_pdf_ai",  # Event name
        data={
        "question": question,
        "top_k": top_k,
        "collection": collection
        }
        )
        response = await inngest_client.send(trigger_event)
        print(response)
        return JSONResponse(content=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying PDF AI: {str(e)}")


inngest.fast_api.serve(
    app,
    inngest_client,
    functions=[rag_ingest_pdf, rag_query_pdf_ai]
)