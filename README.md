# AI Engineering Projects

Personal builds by Sudharsan V S. Each project has its own README, tests and committed evaluation results.

## Projects

- [`ai-market-research-copilot`](ai-market-research-copilot/README.md)
  RAG over uploaded market-research documents. FAISS retrieves 20 candidates, an NVIDIA NIM reranker keeps 6, and a relevance threshold makes the assistant decline questions the documents don't cover. Fixed-size 305-word chunks were chosen by benchmark over semantic chunking ([sweep](ai-market-research-copilot/docs/FIXED_CHUNK_SIZE_SWEEP_2026-08-26.md), [fixed vs semantic](ai-market-research-copilot/docs/CHUNKING_BENCHMARK_2026-08-25.md)).

- [`enterprise-rag`](enterprise-rag/README.md)
  Permission-aware RAG backend: JWT auth, role checks before retrieval so restricted documents never reach the model, pattern-based prompt-injection screening, and an audit log of every query ([RBAC evaluation](enterprise-rag/docs/RBAC_EVALUATION.md)).

- [`aus-weather-rain-prediction`](aus-weather-rain-prediction/)
  Time-aware rainfall classifier with chronological validation, a tuned decision threshold, PSI drift monitoring, Streamlit serving and Docker.

## Running the tests

Each project runs its own suite from its directory:

```bash
cd ai-market-research-copilot && python -m pytest -q
cd enterprise-rag && python -m pytest -q
```
