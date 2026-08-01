"""Demo SQL data generation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import EmployeeRecord, FinanceReport


def seed_enterprise_sql(db: Session) -> None:
    if db.query(EmployeeRecord).first() or db.query(FinanceReport).first():
        return

    db.add_all(
        [
            EmployeeRecord(
                employee_id="E-1001",
                name="Avery Singh",
                department="Engineering",
                title="Platform Engineer",
                manager="Mina Rao",
                salary_band="P4",
                performance_rating="Exceeds",
            ),
            EmployeeRecord(
                employee_id="E-1002",
                name="Jordan Lee",
                department="HR",
                title="People Operations Lead",
                manager="Iris Chen",
                salary_band="M2",
                performance_rating="Meets",
            ),
            FinanceReport(
                quarter="FY26-Q1",
                business_unit="Cloud Infrastructure",
                revenue=1450000.0,
                expenses=980000.0,
                risk_notes="GPU capacity costs increased 11 percent versus plan.",
            ),
            FinanceReport(
                quarter="FY26-Q1",
                business_unit="Enterprise AI",
                revenue=2320000.0,
                expenses=1210000.0,
                risk_notes="Pipeline concentration risk remains medium.",
            ),
        ]
    )
    db.commit()
