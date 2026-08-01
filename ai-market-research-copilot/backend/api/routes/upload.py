import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id, sanitize_upload_filename
from backend.models.db_models import Document
from backend.models.db_models import Session as DBSession
from backend.models.schemas import UploadResponse
from backend.services.chunker import chunk_pages
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

        # Persist document record
        doc = Document(
            session_id=session_id,
            filename=safe_filename,
            file_type=ext.lstrip("."),
            file_path=str(file_path),
            file_size_kb=round(len(content) / 1024, 2),
            chunk_count=len(chunks),
            indexed=True,
        )
        db.add(doc)
        db.commit()

        return UploadResponse(
            session_id=session_id,
            filename=safe_filename,
            file_type=ext.lstrip("."),
            chunk_count=len(chunks),
            message=f"Indexed {len(chunks)} chunks. Total vectors in session: {total_vectors}",
        )

    except Exception as e:
        logger.error(f"[{session_id}] Indexing failed for {safe_filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}") from e


@router.get("/{session_id}/documents")
def list_documents(session_id: str, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.session_id == session_id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size_kb": d.file_size_kb,
            "chunk_count": d.chunk_count,
            "indexed": d.indexed,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.delete("/{session_id}/documents/{doc_id}")
def delete_document(session_id: str, doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.session_id == session_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file
    path = Path(doc.file_path)
    if path.exists():
        path.unlink()

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "filename": doc.filename}
