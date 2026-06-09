# AI Market Research Copilot

Full-stack RAG application for market research workflows. Users can upload documents, generate structured market reports, and ask grounded questions over uploaded content.

This is the strongest AI/backend project in this portfolio because it combines API design, document parsing, embeddings, vector search, LLM orchestration, persistence, reporting, and containerized local deployment.

## What It Does

- Upload and parse PDF, CSV, TXT, and Markdown files.
- Split documents into chunks and create embeddings.
- Store per-session vectors in FAISS.
- Generate market research sections: executive summary, competitors, pricing, trends, and SWOT.
- Support RAG chat over uploaded documents with cited source snippets.
- Generate PDF reports with ReportLab.
- Run with Docker Compose or as separate FastAPI and Streamlit services.

## Architecture

```text
User
  -> Streamlit / React UI
  -> FastAPI backend
  -> document parser
  -> chunker
  -> embedding provider
  -> FAISS vector index
  -> retriever / reranker
  -> LLM provider
  -> report generator
  -> SQLite metadata store
```

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- AI/RAG: FAISS, sentence-transformers, NVIDIA NIM, Gemini, Ollama
- Retrieval: chunking, vector search, optional reranking
- Frontend: Streamlit plus React UI assets
- Reports: ReportLab PDF generation
- Storage: SQLite for metadata, local FAISS indexes per session
- Deployment: Docker, Docker Compose

## API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/upload/` | Upload, parse, chunk, embed, and index a document |
| `GET` | `/api/v1/upload/{session_id}/documents` | List indexed documents |
| `POST` | `/api/v1/research/generate` | Start background market report generation |
| `GET` | `/api/v1/research/{session_id}/reports` | List reports for a session |
| `GET` | `/api/v1/research/{session_id}/reports/{report_id}` | Fetch report data |
| `POST` | `/api/v1/chat/` | Ask questions over indexed documents |
| `GET` | `/health` | Service health and configuration summary |

## Run Locally

```bash
cp .env.example .env
# Add at least one provider key, or configure Ollama locally.

docker-compose up --build
```

Services:

- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

## Run Without Docker

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## Recruiter Notes

This project demonstrates:

- Building an AI application beyond a notebook.
- Designing FastAPI routes around asynchronous report generation.
- Implementing a RAG pipeline with parsing, chunking, embeddings, retrieval, and LLM generation.
- Managing per-session vector indexes and metadata persistence.
- Packaging services for local deployment with Docker Compose.
- Thinking about hallucination control through document grounding, source snippets, and fallback behavior.

## Current Production Gaps

- Add pytest coverage for upload, retrieval, report generation, and chat behavior.
- Add GitHub Actions for linting and tests.
- Replace permissive CORS with environment-specific origins.
- Add API authentication and rate limiting.
- Add RAG evaluation metrics such as recall@k, answer faithfulness, and citation quality.
- Move from local SQLite/FAISS to managed storage for multi-user production workloads.

## Security Note

API keys must be supplied through `.env` or deployment secrets. No provider key should be committed to source control. If a real key was ever committed, rotate it immediately because Git history can preserve deleted secrets.
