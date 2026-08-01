# Sudharsan V S - AI Backend Portfolio

This repository is curated for AI/backend recruiter review. The flagship project is `ai-market-research-copilot`, supported by secure enterprise RAG and time-aware machine learning projects with committed evaluation evidence.

Recruiter-facing summary:

- Role signal: AI Engineer, Backend Engineer, Data/ML application developer.
- Core strengths: Python, FastAPI, RAG, FAISS, sentence-transformers, LLM APIs, RBAC, test coverage, Docker, and security-minded backend work.
- Security signal: explicit CORS origins, optional API-key auth, rate limiting, sanitized uploads, validated session IDs, local env encryption workflow, production JWT secret checks, ignored runtime artifacts, and JSON metadata storage instead of pickle.
- Quality signal: 80 passing automated tests across RAG grounding, API security, background jobs, RBAC, retrieval, observability, temporal ML evaluation, and drift monitoring.

## Projects

- [`ai-market-research-copilot/README.md`](ai-market-research-copilot/README.md)
  Full-stack RAG market research platform with upload, parsing, chunking, vector retrieval, grounded chat, report generation, PDF export, auth, rate limiting, and retrieval eval helpers.

- [`enterprise-rag/README.md`](enterprise-rag/README.md)
  Secure enterprise RAG backend with JWT auth, RBAC retrieval filtering, prompt-injection defense, hybrid retrieval, grounded generation, and audit logging.

- [`aus-weather-rain-prediction/README.md`](aus-weather-rain-prediction/README.md)
  Time-aware rainfall classifier with chronological validation, a tuned decision threshold, 72.1% held-out rain recall, PSI drift monitoring, Streamlit serving, Docker, and CI.

## Recruiter Review

See [`PRIORITY_PROJECT_COMPLETION_REPORT.md`](PRIORITY_PROJECT_COMPLETION_REPORT.md) for verified results, commands, and remaining publication blockers.

Recommended flagship repository name: `ai-market-research-copilot`.

Recommended description: `Full-stack RAG market research platform with FastAPI, FAISS, local embeddings, NVIDIA NIM, a React workspace, and Docker.`
