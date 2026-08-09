import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id, sanitize_upload_filename
from backend.models.db_models import Document
from backend.models.db_models import Session as DBSession
from backend.models.schemas import DocumentBriefResponse, UploadResponse
from backend.services.chunker import chunk_pages
from backend.services.document_brief import build_document_brief
from backend.services.document_parser import parse_document
from backend.services.vector_store import FAISSVectorStore

router = APIRouter(prefix="/upload", tags=["Upload"])
logger = get_logger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".md"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    db: Session = Depends(get_db),
):
    # Validate extension
    safe_filename = sanitize_upload_filename(file.filename)
    ext = Path(safe_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB} MB",
        )

    # Create or reuse session
    if not session_id:
        session_id = str(uuid.uuid4())
    session_id = normalize_session_id(session_id)

    db_session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not db_session:
        db_session = DBSession(session_id=session_id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

    # Save file
    save_dir = settings.UPLOAD_DIR / session_id
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"[{session_id}] Saved upload: {safe_filename} ({len(content) / 1024:.1f} KB)")

    # Parse → chunk → embed → index
    try:
        pages = parse_document(file_path)
        chunks = chunk_pages(pages)

        store = FAISSVectorStore(session_id)
        total_vectors = store.add_chunks(chunks)

        brief = None
        brief_status = "unavailable"
        try:
            brief = await run_in_threadpool(build_document_brief, safe_filename, chunks)
            brief_status = "ready"
        except Exception as brief_error:
            logger.warning(
                "[%s] Source briefing unavailable for %s: %s",
                session_id,
                safe_filename,
                type(brief_error).__name__,
            )

        # Persist document record
        doc = Document(
            session_id=session_id,
            filename=safe_filename,
            file_type=ext.lstrip("."),
            file_path=str(file_path),
            file_size_kb=round(len(content) / 1024, 2),
            chunk_count=len(chunks),
            indexed=True,
            brief=brief,
            brief_status=brief_status,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        return UploadResponse(
            session_id=session_id,
            document_id=doc.id,
            filename=safe_filename,
            file_type=ext.lstrip("."),
            chunk_count=len(chunks),
            brief=brief,
            brief_status=brief_status,
            message=f"Indexed {len(chunks)} chunks. Total vectors in session: {total_vectors}",
        )

    except Exception as e:
        logger.error(f"[{session_id}] Indexing failed for {safe_filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}") from e


@router.get("/{session_id}/documents")
def list_documents(session_id: str, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    docs = db.query(Document).filter(Document.session_id == session_id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size_kb": d.file_size_kb,
            "chunk_count": d.chunk_count,
            "indexed": d.indexed,
            "brief": d.brief,
            "brief_status": d.brief_status or ("ready" if d.brief else "pending"),
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.post(
    "/{session_id}/documents/{doc_id}/brief",
    response_model=DocumentBriefResponse,
)
async def generate_document_brief(
    session_id: str,
    doc_id: int,
    db: Session = Depends(get_db),
):
    """Generate or retry a persisted briefing for an already indexed document."""
    session_id = normalize_session_id(session_id)
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.session_id == session_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.brief and doc.brief_status == "ready":
        return DocumentBriefResponse(
            document_id=doc.id,
            brief=doc.brief,
            brief_status="ready",
        )

    file_path = Path(doc.file_path)
    if not file_path.is_file():
        doc.brief_status = "unavailable"
        db.commit()
        raise HTTPException(status_code=404, detail="Uploaded source file is unavailable")

    try:
        pages = await run_in_threadpool(parse_document, file_path)
        chunks = chunk_pages(pages)
        brief = await run_in_threadpool(build_document_brief, doc.filename, chunks)
    except Exception as error:
        doc.brief_status = "unavailable"
        db.commit()
        logger.warning(
            "[%s] Source briefing retry failed for %s: %s",
            session_id,
            doc.filename,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="The source is indexed, but its AI briefing is temporarily unavailable.",
        ) from error

    doc.brief = brief
    doc.brief_status = "ready"
    db.commit()
    return DocumentBriefResponse(
        document_id=doc.id,
        brief=doc.brief,
        brief_status="ready",
    )


@router.delete("/{session_id}/documents/{doc_id}")
def delete_document(session_id: str, doc_id: int, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.session_id == session_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    removed_chunks = FAISSVectorStore(session_id).remove_document(doc.filename)

    # Remove file
    path = Path(doc.file_path)
    if path.exists():
        path.unlink()

    db.delete(doc)
    db.commit()
    return {
        "status": "deleted",
        "filename": doc.filename,
        "removed_chunks": removed_chunks,
    }
