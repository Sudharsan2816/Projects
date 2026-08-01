"""Security guardrails for retrieved context and generated responses."""

from __future__ import annotations

import re

SENSITIVE_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
    (re.compile(r"salary_band\s*[:=]\s*\w+", re.IGNORECASE), "salary_band=[REDACTED]"),
]


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def ensure_context_available(contexts: list[dict]) -> bool:
    return any(item.get("content", "").strip() for item in contexts)


def access_denied_message(denied_sources: list[str]) -> str:
    joined = ", ".join(sorted(set(denied_sources)))
    return f"Access denied. Your role is not permitted to query: {joined}."
