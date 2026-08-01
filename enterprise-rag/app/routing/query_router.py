"""Map classified intent to retriever source types and RBAC permissions."""

from __future__ import annotations

from app.routing.intent_classifier import classify_intent

INTENT_TO_SOURCES = {
    "pdf": ["pdf", "text"],
    "sql": ["sql"],
    "csv": ["csv"],
    "json": ["json"],
    "hybrid": ["pdf", "text", "sql", "csv", "json"],
}

INTENT_TO_RBAC_HINTS = {
    "pdf": ["technical_docs", "compliance_docs", "policies", "HR_documents", "financial_reports"],
    "sql": ["employee_records", "finance_db"],
    "csv": ["incident_reports"],
    "json": ["logs", "operational_logs", "audit_logs"],
    "hybrid": [
        "technical_docs",
        "logs",
        "incident_reports",
        "compliance_docs",
        "audit_logs",
        "policies",
        "employee_records",
        "HR_documents",
        "financial_reports",
        "finance_db",
        "operational_logs",
    ],
}

PERMISSION_KEYWORDS = {
    "technical_docs": ["architecture", "technical", "engineering", "service design"],
    "compliance_docs": ["compliance", "regulatory", "control requirement"],
    "policies": ["policy", "retention", "exception"],
    "HR_documents": ["hr document", "handbook", "onboarding"],
    "financial_reports": ["financial report", "forecast", "margin"],
    "employee_records": ["employee", "salary", "manager", "performance"],
    "finance_db": ["finance", "revenue", "expense", "quarter"],
    "incident_reports": ["incident", "ticket", "severity", "csv"],
    "logs": ["log", "logs", "server"],
    "operational_logs": ["operational", "outage", "service event"],
    "audit_logs": ["audit trail", "audit event"],
}


def infer_required_permissions(query: str, intent: str) -> list[str]:
    """Narrow broad source permissions using domain terms in the query."""
    lowered = query.lower()
    intent_permissions = set(INTENT_TO_RBAC_HINTS[intent])
    matched = [
        permission
        for permission, keywords in PERMISSION_KEYWORDS.items()
        if permission in intent_permissions and any(keyword in lowered for keyword in keywords)
    ]
    return matched or INTENT_TO_RBAC_HINTS[intent]


def route_query(query: str) -> dict:
    intent = classify_intent(query)
    return {
        "intent": intent,
        "source_types": INTENT_TO_SOURCES[intent],
        "required_permissions": infer_required_permissions(query, intent),
    }
