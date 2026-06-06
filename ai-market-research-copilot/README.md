# AI Market Research Copilot

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-vector--store-blue)
![Gemini](https://img.shields.io/badge/Gemini-1.5--Flash-4285F4?logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow)

> Upload a document or enter a market topic — get a professional, citation-grounded research report with competitor profiles, pricing intelligence, market trends, and SWOT analysis in minutes. Total operational cost: **$0/month**.

---

## The Problem

Market research agencies charge $5,000–$50,000 per report and take 2–4 weeks to deliver. Small and mid-size teams either skip it entirely or make product and positioning decisions on gut feel.

---

## Solution

A full-stack RAG (Retrieval-Augmented Generation) pipeline that:
1. Ingests your documents locally — no data leaves your machine for embedding
2. Chunks, embeds, and indexes them in FAISS in seconds
3. Retrieves relevant context per research section
4. Generates structured intelligence via Gemini 1.5 Flash
5. Exports a professional branded PDF report

Every embedding runs on CPU via `sentence-transformers` — zero cloud cost for vector search.

---

## Architecture

```
Documents (PDF / CSV / TXT / Markdown)
         │
         ▼
  FastAPI  POST /api/v1/upload/
         │
         ├─ Document Parser   extract raw text per file type
         ├─ Chunker           800-token chunks, 100-token overlap
         └─ Embedder          sentence-transformers/all-MiniLM-L6-v2
                              (runs locally on CPU, no API key needed)
                              │
                              ▼
                       FAISS Index (per session, persisted to disk)
                              │
            ┌─────────────────┴──────────────────┐
            │          Research Engine            │
            │   (FastAPI background task)         │
            │                                     │
            │  For each report section:           │
            │  ┌──────────────────────────────┐   │
            │  │  RAG Query                   │   │
            │  │  1. Retrieve top-6 from FAISS│   │
            │  │  2. Build context + prompt   │   │
            │  │  3. Gemini 1.5 Flash → JSON  │   │
            │  └──────────────────────────────┘   │
            │                                     │
            │  Sections (run concurrently):       │
            │  • Top-5 competitor profiles        │
            │  • Segment-level pricing            │
            │  • Top-5 market trends              │
            │  • SWOT analysis                    │
            └──────────────┬──────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     PDF Report (ReportLab)    Streamlit Dashboard
     branded, downloadable     Plotly charts, chat UI
```

---

## Key Features

| Feature | Detail |
|---------|--------|
| **Document ingestion** | PDF, CSV, TXT, Markdown — up to 50 MB |
| **Local embeddings** | `sentence-transformers/all-MiniLM-L6-v2` — runs on CPU, no API key |
| **Vector search** | FAISS in-process — no database to manage |
| **RAG pipeline** | Per-section retrieval ensures grounded, citation-backed output |
| **Competitor analysis** | Extracts top-5 competitor profiles from your documents |
| **Pricing intelligence** | Segment-level pricing extracted from context |
| **Market trends** | Top-5 trends with impact rating and timeframe |
| **SWOT analysis** | AI-generated, grounded in uploaded documents |
| **PDF export** | Branded professional report via ReportLab |
| **Chat interface** | Follow-up questions against indexed documents |
| **Fully offline** | Ollama support (Mistral, Llama 3) for zero cloud dependency |
| **Docker ready** | `docker-compose up` — frontend + backend in one command |

---

## How It Works

**Step 1 — Upload**
User uploads a PDF, CSV, or text file through the Streamlit UI. FastAPI receives it at `POST /api/v1/upload/`.

**Step 2 — Index**
Background task: parse text → chunk (800 tokens, 100-token overlap) → embed via `sentence-transformers` (runs locally) → insert into session-scoped FAISS index. Index persisted to disk between requests.

**Step 3 — Generate Report**
User clicks "Generate Report". FastAPI spawns background tasks for each report section. Each section independently retrieves top-6 relevant chunks from FAISS, builds a structured prompt, calls Gemini 1.5 Flash, and parses the JSON response.

**Step 4 — View and Export**
Streamlit renders results with Plotly charts. User downloads a branded ReportLab PDF with all sections.

**Step 5 — Chat**
User asks follow-up questions. The chat pipeline retrieves relevant chunks from FAISS and returns citation-grounded answers.

---

## Results

| Metric | Value |
|--------|-------|
| Average report generation | 45–90 seconds |
| Embedding cost | $0 (local CPU inference) |
| Vector search cost | $0 (in-process FAISS) |
| LLM cost (Gemini free tier) | $0 (15 req/min, 1M tokens/day) |
| Total operational cost | **$0/month** |
| Max document size | 50 MB |
| Embedding dimensions | 384 (all-MiniLM-L6-v2) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (multi-page, dark theme, Plotly charts) |
| Backend | FastAPI (async, background tasks) |
| Vector Store | FAISS (local, in-process, session-scoped) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | Gemini 1.5 Flash (free tier) + Ollama fallback |
| Database | SQLite + SQLAlchemy (session and report metadata) |
| PDF | ReportLab |
| Deployment | Docker Compose / Render (free) / Streamlit Cloud |

---

## Setup

### Quick Start (Local)

```bash
git clone https://github.com/Sudharsan2816/Projects
cd Projects/ai-market-research-copilot

cp .env.example .env
# Add your GEMINI_API_KEY
# Free key: https://aistudio.google.com/app/apikey

# Backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

### Docker (Recommended)

```bash
cd ai-market-research-copilot
cp .env.example .env   # add GEMINI_API_KEY
docker-compose up --build
```

### Fully Offline with Ollama

```bash
ollama pull mistral

# Set in .env:
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
EMBEDDING_PROVIDER=local

docker-compose up --build
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload/` | Upload and index a document |
| `GET` | `/api/v1/upload/{session_id}/documents` | List indexed documents |
| `POST` | `/api/v1/research/generate` | Trigger report generation |
| `GET` | `/api/v1/research/{session_id}/reports` | List reports |
| `GET` | `/api/v1/research/{session_id}/reports/{id}` | Get report data |
| `GET` | `/api/v1/report/{id}/download` | Download PDF |
| `POST` | `/api/v1/chat/` | Chat with indexed documents |
| `GET` | `/api/v1/chat/{session_id}/history` | Chat history |
| `GET` | `/health` | Health check |

---

## Project Structure

```
ai-market-research-copilot/
├── backend/
│   ├── api/routes/
│   │   ├── upload.py          file upload and FAISS indexing
│   │   ├── research.py        report generation (background tasks)
│   │   ├── chat.py            RAG chat endpoint
│   │   └── report.py          PDF download
│   ├── core/
│   │   ├── config.py          Pydantic settings from .env
│   │   └── database.py        SQLite + SQLAlchemy
│   ├── services/
│   │   ├── document_parser.py PDF / CSV / TXT extraction
│   │   ├── chunker.py         fixed-size chunking with overlap
│   │   ├── embedder.py        sentence-transformers wrapper
│   │   ├── vector_store.py    FAISS index per session
│   │   ├── llm.py             Gemini + Ollama clients
│   │   ├── rag.py             retrieval pipeline
│   │   ├── research_engine.py all report sections
│   │   ├── report_generator.py ReportLab PDF builder
│   │   └── chat_engine.py     chat with history
│   └── main.py
├── frontend/
│   ├── app.py                 dashboard home
│   ├── pages/
│   │   ├── 1_Upload.py        file upload UI
│   │   ├── 2_Research.py      report trigger UI
│   │   ├── 3_Report.py        report viewer + Plotly charts
│   │   └── 4_Chat.py          chat interface
│   └── components/
│       ├── styles.py          global dark CSS
│       ├── sidebar.py         navigation
│       └── charts.py          Plotly chart helpers
├── .env.example
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```
