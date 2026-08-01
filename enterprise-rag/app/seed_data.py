"""Generate realistic demo enterprise data."""

from __future__ import annotations

import json
from pathlib import Path

import fitz
import pandas as pd

from app.config import DATA_DIR
from app.ingestion.pdf_ingestor import ingest_pdf
from app.retrieval.vector_store import vector_store

PDF_FIXTURES = {
    "technical_architecture.pdf": (
        "Enterprise Platform Technical Architecture\n\n"
        "The production platform runs FastAPI services behind an API gateway. "
        "Core services publish operational events to the logging pipeline. "
        "Incident response requires engineers to inspect service logs, outage timelines, "
        "and incident reports. The vector retrieval service indexes approved technical documents."
    ),
    "compliance_manual.pdf": (
        "Compliance Manual\n\n"
        "Compliance teams must review access controls, audit logs, retention policies, "
        "and policy exceptions. Customer confidential data must not be copied into prompts. "
        "Audit trails must include user identity, role, query, sources, and security flags."
    ),
    "hr_policy.pdf": (
        "HR Policy Handbook\n\n"
        "HR documents include onboarding policy, performance review policy, and employee records guidance. "
        "Employee records are restricted to HR and Admin roles. Sensitive personal information must be redacted."
    ),
    "finance_report.pdf": (
        "Finance Reporting Guide\n\n"
        "Finance users may access financial reports and finance database summaries. "
        "Quarterly reporting covers revenue, expenses, margin risk, and forecast assumptions."
    ),
}


def write_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(page.rect + (36, 36, -36, -36), text, fontsize=11)
    document.save(path)
    document.close()


def seed_pdfs() -> int:
    pdf_dir = DATA_DIR / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    indexed_chunks = 0
    for filename, text in PDF_FIXTURES.items():
        path = pdf_dir / filename
        if not path.exists():
            write_pdf(path, text)
        if not vector_store.has_source(path):
            indexed_chunks += ingest_pdf(path)
    return indexed_chunks


def seed_csv() -> int:
    csv_dir = DATA_DIR / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    path = csv_dir / "incident_reports.csv"
    if path.exists():
        return 0
    df = pd.DataFrame(
        [
            {
                "incident_id": "INC-2401",
                "service": "payments-api",
                "severity": "high",
                "summary": "Checkout outage caused by database connection saturation.",
                "status": "resolved",
            },
            {
                "incident_id": "INC-2402",
                "service": "search",
                "severity": "medium",
                "summary": "Elevated latency after index refresh.",
                "status": "monitoring",
            },
            {
                "incident_id": "INC-2403",
                "service": "auth",
                "severity": "critical",
                "summary": "JWT validation errors after key rotation.",
                "status": "resolved",
            },
        ]
    )
    df.to_csv(path, index=False)
    return 1


def seed_json_logs() -> int:
    log_dir = DATA_DIR / "json_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    operational = log_dir / "operational_logs.json"
    audit = log_dir / "audit_trails.json"
    created = 0
    if not operational.exists():
        operational.write_text(
            json.dumps(
                [
                    {
                        "timestamp": "2026-05-12T08:15:00Z",
                        "service": "payments-api",
                        "level": "ERROR",
                        "message": "Database pool exhausted during checkout outage",
                    },
                    {
                        "timestamp": "2026-05-12T08:21:00Z",
                        "service": "payments-api",
                        "level": "INFO",
                        "message": "Failover completed and error rate returned to baseline",
                    },
                    {
                        "timestamp": "2026-05-12T09:05:00Z",
                        "service": "auth",
                        "level": "WARN",
                        "message": "JWT key rotation drift detected in one region",
                    },
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        created += 1
    if not audit.exists():
        audit.write_text(
            json.dumps(
                [
                    {
                        "timestamp": "2026-05-12T10:30:00Z",
                        "actor": "compliance",
                        "action": "view_audit_report",
                        "resource": "access-review-q2",
                    },
                    {
                        "timestamp": "2026-05-12T10:45:00Z",
                        "actor": "admin",
                        "action": "update_policy_exception",
                        "resource": "retention-policy",
                    },
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        created += 1
    return created


def seed_demo_files() -> dict[str, int]:
    return {
        "csv_files_created": seed_csv(),
        "json_files_created": seed_json_logs(),
        "pdf_chunks_indexed": seed_pdfs(),
    }
