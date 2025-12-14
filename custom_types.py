from pydantic import BaseModel
from typing import Optional

class RAGChunkAndSrc(BaseModel):
    chunks: list[str]
    source_id: str = None


class RAGUpsertResult(BaseModel):
    ingested: int


class RAGSearchResult(BaseModel):
    contexts: list[str]
    sources: list[str]


class RAGQueryResult(BaseModel):
    answer: str
    sources: list[str]
    num_contexts: int


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    collection: Optional[str] = "docs" 

class IngestRequest(BaseModel):
    pdf_path: str
    source_id: Optional[str] = None
    collection: Optional[str] = "docs" 
