"""Response generation service."""

from __future__ import annotations

from app.llm.llm_client import llm_client
from app.security.guardrails import ensure_context_available


def generate_response(query: str, contexts: list[dict]) -> str:
    if not ensure_context_available(contexts):
        return "Insufficient authorized enterprise context is available to answer this question."
    return llm_client.generate(query, contexts)
