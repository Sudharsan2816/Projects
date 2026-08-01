# Market Research Copilot Demo

This runbook produces a repeatable five-minute recruiter demo with one configured LLM provider.

## Start

From the project directory:

```powershell
docker compose up --build
```

Open the Copilot interface at `http://localhost:8000` and API documentation at `http://localhost:8000/docs`.

For a local Python run, start the application with `python -m uvicorn backend.main:app --port 8000`.

Confirm provider connectivity first with `python -m scripts.check_llm_providers`.

## Recruiter walkthrough

1. Create a research session and upload a small PDF, CSV, or text document.
2. Ask a question answered by the source and show the returned citations.
3. Ask an unsupported question and show the explicit no-context refusal.
4. Generate a structured market report and export it as PDF.
5. Open `/api/v1/metrics` with the configured API key to show request latency, retrieval, provider, and cost telemetry.

## Evaluation evidence

Run the committed offline evaluation:

```powershell
$env:EMBEDDING_PROVIDER='local'
python -m scripts.run_rag_eval --check-thresholds
```

The command writes `evals/rag_eval_results.json` and `docs/RAG_EVALUATION.md`. The suite fails when retrieval or citation thresholds regress.

## Capture checklist

Record one continuous clip showing source upload, grounded answer, citations, refusal behavior, report generation, and the metrics endpoint. Do not include `.env` contents, API keys, uploaded private data, or provider credentials.
