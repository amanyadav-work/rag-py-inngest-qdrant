# RAG (Retrieval-Augmented Generation) PDF Ingestion and Querying System

## Overview

This project provides a system for ingesting and querying PDF documents using Retrieval-Augmented Generation (RAG) techniques. The system leverages FastAPI for the backend, integrating with `Inngest` for event-driven workflows and utilizing Google's Gemini API for content generation and embedding. It uses Qdrant for efficient vector-based search, enabling scalable PDF ingestion and AI-driven querying of document contents.

## Features

- **PDF Ingestion**: Extracts and chunks text from PDFs and stores the embeddings in a vector database (Qdrant).
- **AI-Powered Queries**: Allows users to query the ingested PDFs using a question, retrieving relevant document chunks using semantic search.
- **Event-Driven**: Utilizes `Inngest` for scalable and asynchronous event handling.
- **Scalable Search**: Leverages vector embeddings for high-quality, fast search results.
  
## Requirements

- Python 3.8+
- Dependencies managed with `uv` (instead of `pip`)
- Environment variables 

## Setup

1. **Clone the repository**:
  ```bash
   git clone https://github.com/your-repo.git
   cd your-repo
   ```


2. **Install Dependencies**
  The project uses `uv` for package management, so use the following command to install dependencies:
  ```bash
  uv install
  ```

  3. **Create a `.env` File**
  Configure the following environment variables:

- `GEMINI_API_KEY=<Your-Gemini-API-Key>`
- `QDRANT_API_KEY=<Your-Qdrant-API-Key>`
- `QDRANT_URL=<Your-Qdrant-URL>`

4. **Running the Application**
To run the application locally, use the following command:

```bash
uv run uvicorn main:app --reload
```

The backend will be available at [http://localhost:8000](http://localhost:8000).

## 1. Ingest PDF

**Endpoint:** `PATCH /ingest-pdf`

**Description:** Ingests a PDF document, extracts text, chunks it, and stores the embeddings in Qdrant for future querying.

**Request Body:**
```json
{
  "pdf_path": "<path-to-pdf>",
  "source_id": "<optional-source-id>",
  "collection": "<collection-name>"
}
```

**Response:** A summary of the ingestion process, including the number of chunks ingested.

---

## 2. Query PDF AI

**Endpoint:** `POST /query-pdf-ai`

**Description:** Queries the ingested PDFs using a question, returning relevant document chunks and sources.

**Request Body:**
```json
{
  "question": "<user-question>",
  "top_k": <number-of-results>,
  "collection": "<collection-name>"
}
```

**Response:**
```json
{
  "answer": "<AI-generated-answer>",
  "sources": ["source1", "source2"],
  "num_contexts": <number-of-contexts>
}
```

---

## Workflow 

### Ingestion Workflow 
When a PDF is uploaded, an **`ingest_pdf`** event is triggered. The document is:
- Loaded 
- Chunked 
- Embedded 
- Stored in the Qdrant vector database 

### Query Workflow 
tWhen a query is made, a **`query_pdf_ai`** event is triggered. The system:
e1. Performs a vector search to find the most relevant document chunks 
e2. Uses Gemini AI to generate a concise answer based on the retrieved context.

   
