# Enterprise RAG Intelligence Assistant

Production-style MVP for a secure enterprise RAG assistant with JWT authentication, RBAC, prompt-injection defense, hybrid retrieval, grounded response generation, and audit logging.

## Features

- FastAPI backend with Swagger docs at `/docs`
- JWT registration and login
- Roles: `Admin`, `Engineer`, `Compliance`, `HR`, `Finance`, `Operations`
- RBAC filtering before retrieval so unauthorized context never reaches the generator
- Hybrid retrieval over PDFs, CSV incident reports, JSON logs, and SQLite records
- FAISS vector search with `sentence-transformers/all-MiniLM-L6-v2`
- Local grounded response fallback, plus optional OpenAI GPT-4o when `OPENAI_API_KEY` is set
- Prompt injection and jailbreak blocking
- SQLite audit log for queries, sources, status, and security flags
- Optional idempotent demo-data seeding for local environments
- Structured JSON request/retrieval logs, request IDs, latency headers, and protected metrics
- Executable RBAC allow/deny evaluation fixtures

## Quick Start

```powershell
cd C:\Users\Welcome\Desktop\Projects\enterprise-rag
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker-compose up --build
```

## Configuration

Create a local `.env` from `.env.example`.

```env
ENVIRONMENT=local
SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
```

`SECRET_KEY` is allowed to fall back only in `local`, `test`, and `development` environments. Any non-local deployment must set an explicit secret before JWT signing works.

Initialize schema without demo data, or seed the complete local fixture set explicitly:

```powershell
python -m app.manage init-db
python -m app.manage seed-demo
```

Set `SEED_DEMO_ON_STARTUP=false` outside controlled demo environments.

## Demo Users

These users are created on startup:

| Username | Password | Role |
|---|---|---|
| admin | AdminPass123! | Admin |
| engineer | EngineerPass123! | Engineer |
| compliance | CompliancePass123! | Compliance |
| hr | HrPass123! | HR |
| finance | FinancePass123! | Finance |
| operations | OperationsPass123! | Operations |

## Example Flow

1. `POST /login`
2. Use the returned bearer token in Swagger Authorize.
3. `POST /query`

Example queries:

- Engineer: `show outage logs for payments api`
- Compliance: `summarize compliance manual audit requirements`
- HR: `fetch employee records`
- Finance: `show finance revenue for FY26 Q1`
- Operations: `show incident report csv for outage`

## Security Rules

- Prompt injection attempts return a security violation response.
- Unauthorized roles receive access denied responses.
- Sensitive-looking values are redacted before response generation.
- Audit logs are visible only to `Admin` and `Compliance`.
- Runtime databases, FAISS indexes, vector metadata, `.env` files, and API keys are ignored by git.

## Quality Gates

```powershell
python -m pytest -q
ruff check app tests
python -m app.evaluation.rbac_eval --check
```

The RBAC command regenerates `evals/rbac_eval_results.json` and `docs/RBAC_EVALUATION.md`. It verifies intent routing and expected allow/deny permission paths before retrieval.

## Architecture and observability

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the authorization boundary and data flow.

- Responses include `X-Request-ID` and `Server-Timing` headers.
- JSON logs contain request/retrieval latency and authorized source counts without logging raw query text.
- `GET /metrics` is limited to Admin and Compliance roles.
- Audit records remain separate from operational logs and retain the user-visible query for governance review.

## Portfolio Readiness

This project is a strong secondary portfolio project after the market-research copilot. Multi-node production would still require managed databases/vector storage, centralized telemetry, and versioned schema migrations.
