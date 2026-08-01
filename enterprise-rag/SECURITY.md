# Security Notes

This project is designed as a portfolio-grade secure RAG backend, not a production deployment template.

## Protected Data

Do not commit:

- `.env` files
- OpenAI/API keys
- JWT secrets
- SQLite databases
- FAISS indexes
- vector metadata
- audit logs
- real enterprise documents

The project `.gitignore` excludes these runtime artifacts.

## Authentication

JWT signing uses `SECRET_KEY`. A development-only fallback is available only when `ENVIRONMENT` is `local`, `test`, or `development`; non-local environments fail fast if `SECRET_KEY` is missing.

## RAG Safety

Retrieval is filtered by role before response generation, prompt-injection attempts are blocked, and sensitive-looking values are redacted before model use.
