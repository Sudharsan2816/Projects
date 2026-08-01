import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id
from backend.models.db_models import Report

router = APIRouter(prefix="/report", tags=["Report Export"])
logger = get_logger(__name__)
settings = get_settings()


@router.get("/{session_id}/{report_id}/download")
def download_report(session_id: str, report_id: int, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.session_id == session_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "done":
        raise HTTPException(status_code=400, detail=f"Report not ready (status: {report.status})")

    reports_root = settings.REPORTS_DIR.resolve()
    path = Path(report.report_path).resolve()
    try:
        path.relative_to(reports_root)
    except ValueError as exc:
        logger.warning("Blocked report download outside reports directory: %s", path)
        raise HTTPException(status_code=404, detail="PDF file not found on disk") from exc
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    safe_topic = re.sub(r"[^A-Za-z0-9_-]+", "_", report.topic[:30]).strip("_") or "report"

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"market_research_{safe_topic}.pdf",
    )
