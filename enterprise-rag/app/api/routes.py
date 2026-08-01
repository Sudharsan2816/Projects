"""FastAPI route definitions."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import authenticate_user, create_access_token, hash_password
from app.config import DATA_DIR, settings
from app.dependencies import get_audit_db, get_auth_db, get_current_user, get_enterprise_db
from app.ingestion.csv_ingestor import validate_csv
from app.ingestion.json_ingestor import validate_json
from app.ingestion.pdf_ingestor import ingest_pdf
from app.llm.response_generator import generate_response
from app.logging.audit_logger import list_audit_logs, write_audit_log
from app.models import User
from app.observability import metrics
from app.retrieval.hybrid_retriever import retrieve_context
from app.routing.query_router import route_query
from app.schemas import (
    AuditLogResponse,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    RegisterRequest,
    TokenResponse,
    UploadResponse,
    UserResponse,
)
from app.security.guardrails import access_denied_message
from app.security.prompt_injection import detect_prompt_injection
from app.security.rbac import allowed_permissions, normalize_role

router = APIRouter()


def save_upload(upload: UploadFile, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "upload.bin").name
    target = directory / safe_name
    with target.open("wb") as out_file:
        shutil.copyfileobj(upload.file, out_file)
    return target


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


@router.get("/metrics")
def application_metrics(current_user: User = Depends(get_current_user)) -> dict:
    if current_user.role not in {"Admin", "Compliance"}:
        raise HTTPException(status_code=403, detail="Metrics require Admin or Compliance role")
    return metrics.snapshot()


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_auth_db)) -> UserResponse:
    role = normalize_role(payload.role)
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=payload.username, hashed_password=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(id=user.id, username=user.username, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_auth_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token({"sub": user.username, "role": user.role, "user_id": user.id})
    return TokenResponse(access_token=token, role=user.role)


@router.post("/upload/pdf", response_model=UploadResponse)
def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admin users can ingest documents")
    path = save_upload(file, DATA_DIR / "pdfs")
    chunks = ingest_pdf(path)
    return UploadResponse(filename=path.name, source_type="pdf", status="indexed", indexed_chunks=chunks)


@router.post("/upload/csv", response_model=UploadResponse)
def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admin users can ingest CSV files")
    path = save_upload(file, DATA_DIR / "csv")
    rows = validate_csv(path)
    return UploadResponse(filename=path.name, source_type="csv", status=f"stored {rows} rows")


@router.post("/upload/json", response_model=UploadResponse)
def upload_json(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admin users can ingest JSON files")
    path = save_upload(file, DATA_DIR / "json_logs")
    events = validate_json(path)
    return UploadResponse(filename=path.name, source_type="json", status=f"stored {events} events")


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    enterprise_db: Session = Depends(get_enterprise_db),
    audit_db: Session = Depends(get_audit_db),
) -> QueryResponse:
    flags = detect_prompt_injection(payload.query)
    if flags:
        metrics.record_outcome("security_violation")
        write_audit_log(audit_db, current_user, payload.query, [], "security_violation", flags)
        return QueryResponse(
            answer="Security violation: prompt injection or jailbreak attempt detected.",
            intent="blocked",
            sources=[],
            status="security_violation",
            security_flags=flags,
        )

    route = route_query(payload.query)
    user_permissions = allowed_permissions(current_user.role)
    unauthorized = [
        permission for permission in route["required_permissions"] if permission not in user_permissions
    ]

    if len(unauthorized) == len(route["required_permissions"]):
        metrics.record_outcome("access_denied")
        write_audit_log(audit_db, current_user, payload.query, [], "access_denied", unauthorized)
        return QueryResponse(
            answer=access_denied_message(unauthorized),
            intent=route["intent"],
            sources=[],
            status="access_denied",
            security_flags=unauthorized,
        )

    contexts = retrieve_context(payload.query, current_user.role, route["source_types"], enterprise_db)
    sources = sorted({str(item.get("source")) for item in contexts})
    answer = generate_response(payload.query, contexts)
    status_value = "answered" if contexts else "insufficient_context"
    metrics.record_outcome(status_value)
    write_audit_log(audit_db, current_user, payload.query, sources, status_value, [])

    return QueryResponse(
        answer=answer,
        intent=route["intent"],
        sources=sources,
        status=status_value,
        security_flags=[],
    )


@router.get("/audit", response_model=list[AuditLogResponse])
def audit_logs(
    current_user: User = Depends(get_current_user),
    audit_db: Session = Depends(get_audit_db),
) -> list[AuditLogResponse]:
    if current_user.role not in {"Admin", "Compliance"}:
        raise HTTPException(status_code=403, detail="Audit logs require Admin or Compliance role")
    rows = list_audit_logs(audit_db)
    return [
        AuditLogResponse(
            id=row.id,
            user_id=row.user_id,
            username=row.username,
            role=row.role,
            query=row.query,
            retrieval_sources=row.retrieval_sources,
            response_status=row.response_status,
            security_flags=row.security_flags,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]
