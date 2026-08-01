"""Compatibility exports for security helpers."""

from app.security.guardrails import (
    access_denied_message,
    ensure_context_available,
    redact_sensitive_text,
)
from app.security.prompt_injection import detect_prompt_injection
from app.security.rbac import can_access, filter_authorized_sources

__all__ = [
    "access_denied_message",
    "can_access",
    "detect_prompt_injection",
    "ensure_context_available",
    "filter_authorized_sources",
    "redact_sensitive_text",
]
