"""SQLite-backed audit logging."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def write_audit_log(
    db: Session,
    user: User | None,
    query: str,
    retrieval_sources: list[str],
    response_status: str,
    security_flags: list[str],
) -> AuditLog:
    entry = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else None,
        role=user.role if user else None,
        query=query,
        retrieval_sources=json.dumps(retrieval_sources),
        response_status=response_status,
        security_flags=json.dumps(security_flags),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
