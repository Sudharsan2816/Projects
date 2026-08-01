"""Keyword-first intent classification."""

from __future__ import annotations

INTENT_KEYWORDS: dict[str, list[str]] = {
    "json": ["log", "logs", "audit trail", "event", "outage", "server", "operational"],
    "csv": ["csv", "incident", "incident report", "metrics", "severity", "ticket"],
    "sql": ["employee", "finance", "revenue", "salary", "manager", "quarter", "expense", "record"],
    "pdf": ["pdf", "document", "report", "manual", "policy", "compliance", "architecture", "summarize"],
}


def classify_intent(query: str) -> str:
    lowered = query.lower()
    scores = {
        intent: sum(1 for keyword in keywords if keyword in lowered)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    return best_intent if best_score else "hybrid"
