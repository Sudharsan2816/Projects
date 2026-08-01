"""SQL retriever for structured enterprise records."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import EmployeeRecord, FinanceReport


def retrieve_sql_context(query: str, db: Session, allowed_permissions: set[str]) -> list[dict]:
    lowered = query.lower()
    contexts: list[dict] = []

    if "employee_records" in allowed_permissions and any(
        token in lowered for token in ["employee", "hr", "manager", "salary", "performance"]
    ):
        rows = db.query(EmployeeRecord).limit(10).all()
        for row in rows:
            contexts.append(
                {
                    "source": "employee_records",
                    "source_type": "sql",
                    "permission": "employee_records",
                    "content": (
                        f"Employee {row.employee_id}: {row.name}, {row.title}, "
                        f"department={row.department}, manager={row.manager}, "
                        f"salary_band={row.salary_band}, performance={row.performance_rating}"
                    ),
                }
            )

    if "finance_db" in allowed_permissions and any(
        token in lowered for token in ["finance", "revenue", "expense", "financial", "quarter"]
    ):
        rows = db.query(FinanceReport).limit(10).all()
        for row in rows:
            contexts.append(
                {
                    "source": "finance_reports",
                    "source_type": "sql",
                    "permission": "finance_db",
                    "content": (
                        f"{row.quarter} {row.business_unit}: revenue={row.revenue}, "
                        f"expenses={row.expenses}, risk_notes={row.risk_notes}"
                    ),
                }
            )

    return contexts
