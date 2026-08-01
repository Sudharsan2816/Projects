"""Prompt injection and jailbreak detection."""

from __future__ import annotations

import re

BLOCKED_RULES: dict[str, list[re.Pattern[str]]] = {
    "ignore_previous_instructions": [
        re.compile(r"\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|earlier|above)\s+(instructions|rules|context|system)\b"),
        re.compile(r"\bignore\s+all\s+previous\s+instructions\b"),
    ],
    "secrets_or_hidden_context": [
        re.compile(r"\b(reveal|show|print|display|dump|exfiltrate)\s+(hidden|confidential|secret|system|developer)\b"),
        re.compile(r"\b(system\s+prompt|developer\s+message|hidden\s+data|confidential\s+records?)\b"),
    ],
    "permission_bypass": [
        re.compile(r"\b(bypass|disable|turn\s+off|remove)\s+(permissions?|rbac|security|access\s+control|guardrails?)\b"),
    ],
    "jailbreak": [
        re.compile(r"\b(jailbreak|developer\s+mode|dan\s+mode|unfiltered\s+mode)\b"),
    ],
}


def _normalize(query: str) -> str:
    return re.sub(r"\s+", " ", query.lower()).strip()


def detect_prompt_injection(query: str) -> list[str]:
    text = _normalize(query)
    flags = []
    for rule_name, patterns in BLOCKED_RULES.items():
        if any(pattern.search(text) for pattern in patterns):
            flags.append(rule_name)
    return flags
