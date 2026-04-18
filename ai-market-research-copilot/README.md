# 🔬 AI Market Research Copilot

A full-stack AI-powered market research tool. Upload documents or enter a market topic — get a professional, citation-backed report in minutes.

---

## Features

| Feature | Details |
|---|---|
| 📁 File Upload | PDF, CSV, TXT, Markdown |
| 🧩 Chunking & Embedding | sentence-transformers (local, free) |
| 🔍 Vector Search | FAISS (local, no cloud needed) |
| 🤖 RAG Pipeline | Retrieval-augmented generation |
| 🏢 Competitors | Extract top-5 competitor profiles |
| 💰 Pricing | Segment-level pricing intelligence |
| 📈 Trends | Top-5 market trends with impact/timeframe |
| ⚔️ SWOT | AI-generated SWOT analysis |
| 📄 PDF Export | Professional branded PDF report |
| 💬 Chat | Ask questions about uploaded documents |

---

## Tech Stack

- **Frontend**: Streamlit (multi-page app, dark theme, Plotly charts)
- **Backend**: FastAPI (async, background tasks, REST API)
- **Vector DB**: FAISS (local, in-process)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (runs locally, free)
- **LLM**: Google Gemini 1.5 Flash (free tier) with Ollama fallback
- **Database**: SQLite + SQLAlchemy
- **PDF**: ReportLab
- **Deployment**: Render (free) / Streamlit Cloud / Docker

---

## Quick Start — Local

### 1. Clone & setup

```bash
git clone https://github.com/yourname/ai-market-research-copilot
cd ai-market-research-copilot
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a **free** Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Run the Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Backend will be at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 4. Run the Frontend (new terminal)

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Frontend will be at: http://localhost:8501

---

## Docker Deployment

### Prerequisites
- Docker + Docker Compose installed
- `.env` file configured with your API key

### Run with Docker Compose

```bash
# Build and start both services
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down
```

- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Deployment — Render (Free)

### Backend (FastAPI on Render)

1. Push code to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your repo
4. Settings:
   - **Root directory**: `.`
   - **Build command**: `pip install -r backend/requirements.txt`
   - **Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
   - **Environment variables**: Add all vars from `.env`
5. Deploy

### Frontend (Streamlit Cloud — Free)

1. Go to https://streamlit.io/cloud
2. Connect GitHub repo
3. Set **Main file path**: `frontend/app.py`
4. Add secrets in Streamlit Cloud dashboard:
   ```toml
   BACKEND_URL = "https://your-render-backend.onrender.com"
   ```
5. Deploy

---

## Using Ollama (Fully Offline / Free)

If you don't want to use Gemini API:

```bash
# Install Ollama
# Windows/Mac: https://ollama.com/download
# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull mistral

# Update .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## Project Structure

```
ai-market-research-copilot/
├── backend/
│   ├── api/routes/
│   │   ├── upload.py         # File upload & indexing
│   │   ├── research.py       # Report generation (background)
│   │   ├── chat.py           # RAG chat endpoint
│   │   └── report.py         # PDF download
│   ├── core/
│   │   ├── config.py         # Pydantic settings + .env
│   │   ├── database.py       # SQLite + SQLAlchemy
│   │   └── logging.py        # Structured logger
│   ├── models/
│   │   ├── db_models.py      # ORM models
│   │   └── schemas.py        # Pydantic schemas
│   ├── services/
│   │   ├── document_parser.py  # PDF/CSV/TXT parsing
│   │   ├── chunker.py          # Text chunking with overlap
│   │   ├── embedder.py         # sentence-transformers
│   │   ├── vector_store.py     # FAISS index per session
│   │   ├── llm.py              # Gemini + Ollama clients
│   │   ├── rag.py              # RAG pipeline
│   │   ├── research_engine.py  # All research sections
│   │   ├── report_generator.py # ReportLab PDF builder
│   │   └── chat_engine.py      # Chat with history
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app.py                  # Dashboard (home)
│   ├── pages/
│   │   ├── 1_Upload.py         # File upload UI
│   │   ├── 2_Research.py       # Report generation UI
│   │   ├── 3_Report.py         # Report viewer + charts
│   │   └── 4_Chat.py           # Chat interface
│   ├── components/
│   │   ├── styles.py           # Global dark CSS
│   │   ├── sidebar.py          # Navigation sidebar
│   │   └── charts.py           # Plotly chart components
│   └── requirements.txt
├── data/
│   ├── uploads/                # Uploaded files (per session)
│   ├── indexes/                # FAISS indexes (per session)
│   └── db/                     # SQLite database
├── reports/                    # Generated PDF reports
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload/` | Upload & index a document |
| `GET` | `/api/v1/upload/{session_id}/documents` | List indexed docs |
| `POST` | `/api/v1/research/generate` | Trigger report generation |
| `GET` | `/api/v1/research/{session_id}/reports` | List reports |
| `GET` | `/api/v1/research/{session_id}/reports/{id}` | Get report data |
| `GET` | `/api/v1/report/{id}/download` | Download PDF |
| `POST` | `/api/v1/chat/` | Chat with docs |
| `GET` | `/api/v1/chat/{session_id}/history` | Get chat history |
| `GET` | `/health` | Backend health check |

Interactive docs: http://localhost:8000/docs

---

## Cost

| Component | Cost |
|---|---|
| Gemini 1.5 Flash | Free (15 req/min, 1M tokens/day) |
| sentence-transformers | Free (runs locally) |
| FAISS | Free (runs locally) |
| SQLite | Free |
| Render free tier | Free (spins down after 15 min idle) |
| Streamlit Cloud | Free |
| **Total** | **$0/month** |
