"""Idempotent schema initialization and demo-data seeding."""

from __future__ import annotations

from app.auth import hash_password
from app.ingestion.sql_ingestor import seed_enterprise_sql
from app.models import (
    AuthSessionLocal,
    EmployeeRecord,
    EnterpriseSessionLocal,
    FinanceReport,
    User,
    init_databases,
)
from app.security.rbac import normalize_role
from app.seed_data import seed_demo_files

DEMO_USERS = [
    ("admin", "AdminPass123!", "Admin"),
    ("engineer", "EngineerPass123!", "Engineer"),
    ("compliance", "CompliancePass123!", "Compliance"),
    ("hr", "HrPass123!", "HR"),
    ("finance", "FinancePass123!", "Finance"),
    ("operations", "OperationsPass123!", "Operations"),
]


def seed_demo_users() -> int:
    created = 0
    db = AuthSessionLocal()
    try:
        for username, password, role in DEMO_USERS:
            if not db.query(User).filter(User.username == username).first():
                db.add(
                    User(
                        username=username,
                        hashed_password=hash_password(password),
                        role=normalize_role(role),
                    )
                )
                created += 1
        db.commit()
    finally:
        db.close()
    return created


def initialize_schema() -> None:
    init_databases()


def seed_demo_dataset() -> dict[str, int]:
    initialize_schema()
    users_created = seed_demo_users()
    file_counts = seed_demo_files()
    enterprise_db = EnterpriseSessionLocal()
    try:
        seed_enterprise_sql(enterprise_db)
        sql_records = enterprise_db.query(EmployeeRecord).count() + enterprise_db.query(FinanceReport).count()
    finally:
        enterprise_db.close()
    return {"users_created": users_created, "sql_records": sql_records, **file_counts}
