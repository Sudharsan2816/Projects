"""Hybrid retrieval orchestration."""

from __future__ import annotations

from time import perf_counter

from sqlalchemy.orm import Session

from app.observability import record_retrieval
from app.retrieval.csv_retriever import retrieve_csv_context
from app.retrieval.json_retriever import retrieve_json_context
from app.retrieval.sql_retriever import retrieve_sql_context
from app.retrieval.vector_store import vector_store
from app.security.guardrails import redact_sensitive_text
from app.security.rbac import allowed_permissions


def retrieve_context(query: str, role: str, source_types: list[str], db: Session) -> list[dict]:
    started = perf_counter()
    permissions = allowed_permissions(role)
    contexts: list[dict] = []

    if "pdf" in source_types or "text" in source_types:
        contexts.extend(vector_store.search(query, permissions, top_k=6))
    if "sql" in source_types:
        contexts.extend(retrieve_sql_context(query, db, permissions))
    if "csv" in source_types:
        contexts.extend(retrieve_csv_context(query, permissions))
    if "json" in source_types:
        contexts.extend(retrieve_json_context(query, permissions))

    secured: list[dict] = []
    for item in contexts:
        copy = item.copy()
        copy["content"] = redact_sensitive_text(copy.get("content", ""))
        secured.append(copy)
    record_retrieval(
        query=query,
        role=role,
        source_types=source_types,
        contexts=secured,
        duration_ms=(perf_counter() - started) * 1000,
    )
    return secured
