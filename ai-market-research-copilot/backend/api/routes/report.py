from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.db_models import Report
from backend.core.logging import get_logger

router = APIRouter(prefix="/report", tags=["Report Export"])
logger = get_logger(__name__)


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "done":
        raise HTTPException(status_code=400, detail=f"Report not ready (status: {report.status})")

    path = Path(report.report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=f"market_research_{report.topic[:30].replace(' ', '_')}.pdf",
    )
