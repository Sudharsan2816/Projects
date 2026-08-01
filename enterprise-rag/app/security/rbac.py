"""Role-based access control."""

from __future__ import annotations

PERMISSION_MATRIX: dict[str, set[str]] = {
    "Admin": {
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
    },
    "Engineer": {"technical_docs", "logs", "incident_reports"},
    "Compliance": {"compliance_docs", "audit_logs", "policies"},
    "HR": {"employee_records", "HR_documents"},
    "Finance": {"financial_reports", "finance_db"},
    "Operations": {"operational_logs", "incident_reports"},
}

SOURCE_TO_PERMISSION: dict[str, str] = {
    "pdf": "technical_docs",
    "technical_docs": "technical_docs",
    "compliance_docs": "compliance_docs",
    "policies": "policies",
    "HR_documents": "HR_documents",
    "incident_reports": "incident_reports",
    "logs": "logs",
    "operational_logs": "operational_logs",
    "audit_logs": "audit_logs",
    "employee_records": "employee_records",
    "financial_reports": "financial_reports",
    "finance_db": "finance_db",
    "csv": "incident_reports",
    "json": "logs",
    "sql": "employee_records",
}

VALID_ROLES = set(PERMISSION_MATRIX)


def normalize_role(role: str) -> str:
    role_clean = role.strip()
    for valid_role in VALID_ROLES:
        if role_clean.lower() == valid_role.lower():
            return valid_role
    raise ValueError(f"Invalid role: {role}")


def allowed_permissions(role: str) -> set[str]:
    return PERMISSION_MATRIX.get(normalize_role(role), set())


def can_access(role: str, permission: str) -> bool:
    return permission in allowed_permissions(role)


def filter_authorized_sources(role: str, sources: list[str]) -> tuple[list[str], list[str]]:
    authorized: list[str] = []
    denied: list[str] = []
    for source in sources:
        permission = SOURCE_TO_PERMISSION.get(source, source)
        if can_access(role, permission):
            authorized.append(source)
        else:
            denied.append(source)
    return authorized, denied
