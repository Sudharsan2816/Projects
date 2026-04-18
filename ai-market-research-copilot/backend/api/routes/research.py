import json
import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.db_models import Session as DBSession, Report
from backend.models.schemas import ResearchRequest, ReportResponse, StatusResponse
from backend.services.research_engine import generate_full_report
from backend.services.report_generator import generate_pdf_report
from backend.core.logging import get_logger

router = APIRouter(prefix="/research", tags=["Research"])
logger = get_logger(__name__)


def _run_report(session_id: str, topic: str, report_id: int, db: Session):
    """Background task: generate full report and update DB."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return

    try:
        report.status = "generating"
        db.commit()

        data = generate_full_report(session_id, topic)

        # Generate PDF
        pdf_path = generate_pdf_report(
            session_id=session_id,
            topic=topic,
            executive_summary=data["executive_summary"],
            competitors=data["competitors"],
            pricing_insights=data["pricing_insights"],
            market_trends=data["market_trends"],
            swot_analysis=data["swot_analysis"],
        )

        report.executive_summary = data["executive_summary"]
        report.competitors = json.dumps(data["competitors"])
        report.pricing_insights = json.dumps(data["pricing_insights"])
        report.market_trends = json.dumps(data["market_trends"])
        report.swot_analysis = json.dumps(data["swot_analysis"])
        report.report_path = str(pdf_path)
        report.status = "done"
        db.commit()
        logger.info(f"[{session_id}] Report {report_id} completed")

    except Exception as e:
        logger.error(f"[{session_id}] Report {report_id} failed: {e}")
        report.status = "failed"
        db.commit()


@router.post("/generate", response_model=StatusResponse)
async def generate_report(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Ensure session exists
    db_session = db.query(DBSession).filter(
        DBSession.session_id == request.session_id
    ).first()
    if not db_session:
        db_session = DBSession(session_id=request.session_id, topic=request.topic)
        db.add(db_session)
        db.commit()
    else:
        db_session.topic = request.topic
        db.commit()

    # Create report record
    report = Report(
        session_id=request.session_id,
        topic=request.topic,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    background_tasks.add_task(
        _run_report, request.session_id, request.topic, report.id, db
    )

    return StatusResponse(
        status="accepted",
        message="Report generation started",
        data={"report_id": report.id},
    )


@router.get("/{session_id}/reports")
def list_reports(session_id: str, db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.session_id == session_id).order_by(
        Report.created_at.desc()
    ).all()
    return [_serialize_report(r) for r in reports]


@router.get("/{session_id}/reports/{report_id}")
def get_report(session_id: str, report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(
        Report.id == report_id, Report.session_id == session_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _serialize_report(report)


def _serialize_report(r: Report) -> dict:
    return {
        "id": r.id,
        "session_id": r.session_id,
        "topic": r.topic,
        "status": r.status,
        "executive_summary": r.executive_summary,
        "competitors": json.loads(r.competitors) if r.competitors else None,
        "pricing_insights": json.loads(r.pricing_insights) if r.pricing_insights else None,
        "market_trends": json.loads(r.market_trends) if r.market_trends else None,
        "swot_analysis": json.loads(r.swot_analysis) if r.swot_analysis else None,
        "report_path": r.report_path,
        "created_at": r.created_at,
    }
