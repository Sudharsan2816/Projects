# AI Market Research Copilot

Full-stack RAG application for market research workflows. Users can upload documents, generate structured market reports, and ask grounded questions over uploaded content.

This is the strongest AI/backend project in this portfolio because it combines API design, document parsing, embeddings, vector search, LLM orchestration, persistence, reporting, and containerized local deployment.

## What It Does

- Upload and parse PDF, CSV, TXT, and Markdown files.
- Generate a persisted, document-grounded source brief immediately after indexing.
- Split documents into chunks and create embeddings.
- Store per-session vectors in FAISS.
- Generate market research sections: executive summary, competitors, pricing, trends, and SWOT.
- Support cited RAG chat over uploaded documents plus labeled general market-research guidance.
- Combine thresholded dense retrieval with exact-term fallback for report facts and follow-up questions.
- Generate PDF reports with ReportLab.
- Run one canonical React workspace from the FastAPI service on port 8000.
- Refuse unrelated questions while allowing in-scope market-research questions to use clearly labeled general model knowledge when document context is unavailable or weak.

## Architecture

```text
User
  -> React UI served by FastAPI
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
- Frontend: React workspace served as same-origin static assets
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
| `GET` | `/api/v1/report/{session_id}/{report_id}/download` | Download a session-scoped PDF |
| `POST` | `/api/v1/chat/` | Ask cited document questions or in-scope general market-research questions |
| `GET` | `/health` | Service health and configuration summary |

## Run Locally

```bash
cp .env.example .env
# Set NVIDIA_API_KEY. NVIDIA is the only active provider by default.

docker-compose up --build
```

Services:

- Copilot UI and backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## API Protection

Local development is open by default. To require API credentials for `/api/v1/...` routes, set:

```bash
API_AUTH_TOKEN=replace_with_a_long_random_token
```

Clients can send either:

```text
X-API-Key: replace_with_a_long_random_token
```

or:

```text
Authorization: Bearer replace_with_a_long_random_token
```

Rate limiting is enabled by default with:

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

`/health` stays public by default so deployment health checks continue to work.

## Run Without Docker

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Before a demo, verify the active NVIDIA provider without printing the key or generated content:

```powershell
python -m scripts.check_llm_providers --provider nvidia
```

Fallbacks are disabled by default. To enable them later, set a comma-separated list such as
`LLM_FALLBACK_PROVIDERS=gemini,ollama`.

## Recruiter Notes

This project demonstrates:

- Building an AI application beyond a notebook.
- Designing FastAPI routes around asynchronous report generation.
- Implementing a RAG pipeline with parsing, chunking, embeddings, retrieval, and LLM generation.
- Managing per-session vector indexes and metadata persistence.
- Packaging services for local deployment with Docker Compose.
- Thinking about hallucination control through document grounding, source snippets, and strict no-context behavior.
- Hardening common backend risks: upload filename sanitization, session path validation, explicit CORS origins, and JSON metadata instead of pickle.

## Quality Gates

```bash
python -m pytest -q
```

Current focused coverage includes:

- Provider-key defaults are not hardcoded.
- CORS defaults are not wildcard-with-credentials.
- Optional API-key auth accepts `X-API-Key` and bearer tokens.
- In-memory rate limiter blocks clients after configured capacity.
- Upload filenames and session IDs are path-safe.
- Chunking preserves source metadata.
- Strict RAG does not call the LLM when no indexed context is retrieved.
- Hybrid chat uses general knowledge only for market-research questions and refuses unrelated prompts.
- RAG retrieval metric helpers compute recall@k and hit@k.

## RAG Evaluation

A starter golden set lives at `evals/rag_golden_set.json`. Add real labeled questions in this format:

```json
{
  "id": "case-id",
  "question": "Question users will ask",
  "relevant_chunk_ids": ["source.pdf::3"]
}
```

Run the committed embedding-based fixture suite and regenerate the JSON plus Markdown report:

```bash
python -m scripts.run_rag_eval --check-thresholds
```

The report covers recall@k, hit@k, deterministic answer faithfulness, citation precision, citation recall, and per-case failures. Use the helpers in `backend/evaluation/` to score retrieval before judging final answer quality. The minimum useful evaluation loop is:

1. Upload a fixed test document set.
2. Ask each golden question.
3. Save the retrieved chunk IDs.
4. Compute recall@k and hit@k.
5. Review low-recall cases and tune chunking, metadata, embedding model, or reranking.

See [`docs/RAG_EVALUATION.md`](docs/RAG_EVALUATION.md) for the latest committed results and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the request and retrieval architecture.

## Observability

- Every request receives an `X-Request-ID` response header and a `Server-Timing` duration.
- JSON logs include request IDs, status, latency, retrieval candidates, selected sources, provider/model, estimated tokens, and estimated cost.
- Query text is not logged; retrieval traces use a short SHA-256 fingerprint.
- `GET /api/v1/metrics` returns process-local request, retrieval, and provider summaries and follows the optional API-key protection.
- Set `LLM_INPUT_COST_PER_MILLION` and `LLM_OUTPUT_COST_PER_MILLION` for the configured model to enable estimated spend.

## Current Production Gaps

- Add broader pytest coverage for upload API, retrieval integration, and streaming chat.
- Expand the labeled evaluation set with real customer documents and an independent model-based judge.
- Move from local SQLite/FAISS to managed storage for multi-user production workloads.

## Security Note

API keys must be supplied through `.env` or deployment secrets. No provider key should be committed to source control. If a real key was ever committed, rotate it immediately because Git history can preserve deleted secrets.

Local encryption workflow:

```bash
python scripts/env_vault.py encrypt --input .env --output .env.enc --key-file .env.key
python scripts/env_vault.py decrypt --input .env.enc --output .env --key-file .env.key
```

Both `.env.enc` and `.env.key` are ignored by default. Keep `.env.key` outside Git and back it up securely if you rely on the encrypted copy. The plaintext `.env` is still needed when running the app locally, so delete or move it only when you are not actively using the local services.
