import json
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import SessionLocal, get_db
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id
from backend.models.db_models import Report
from backend.models.db_models import Session as DBSession
from backend.models.schemas import ResearchRequest, StatusResponse
from backend.services.llm import LLMProviderError
from backend.services.report_generator import generate_pdf_report
from backend.services.research_engine import generate_full_report

router = APIRouter(prefix="/research", tags=["Research"])
logger = get_logger(__name__)
settings = get_settings()

_executor = ThreadPoolExecutor(
    max_workers=max(1, settings.REPORT_WORKER_COUNT),
    thread_name_prefix="market-report",
)
_active_report_ids: set[int] = set()
_active_lock = Lock()


class ReportQueueFullError(RuntimeError):
    pass


def _set_progress(report_id: int, progress: int, stage: str) -> None:
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return
        report.progress = max(0, min(100, progress))
        report.current_stage = stage[:80]
        report.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def _public_failure_message(error: Exception) -> str:
    if isinstance(error, LLMProviderError):
        return str(error)
    if "reportlab" in error.__class__.__module__.lower():
        return "The analysis completed, but PDF rendering failed. Retry the report."
    return "Report generation failed unexpectedly. Check server logs and retry."


def _run_report(session_id: str, topic: str, report_id: int) -> None:
    """Generate a report independently of the originating browser request."""
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report or report.status == "done":
            return

        report.status = "generating"
        report.progress = 2
        report.current_stage = "Starting analysis"
        report.error_message = None
        report.updated_at = datetime.utcnow()
        db.commit()

        data = generate_full_report(
            session_id,
            topic,
            on_progress=lambda progress, stage: _set_progress(report_id, progress, stage),
        )

        _set_progress(report_id, 92, "Rendering PDF")
        pdf_path = generate_pdf_report(
            session_id=session_id,
            topic=topic,
            executive_summary=data["executive_summary"],
            competitors=data["competitors"],
            pricing_insights=data["pricing_insights"],
            market_trends=data["market_trends"],
            swot_analysis=data["swot_analysis"],
            data_source=data.get("data_source", "web_search+llm"),
        )

        db.refresh(report)
        report.executive_summary = data["executive_summary"]
        report.competitors = json.dumps(data["competitors"])
        report.pricing_insights = json.dumps(data["pricing_insights"])
        report.market_trends = json.dumps(data["market_trends"])
        report.swot_analysis = json.dumps(data["swot_analysis"])
        report.report_path = str(pdf_path)
        report.status = "done"
        report.progress = 100
        report.current_stage = "Report ready"
        report.error_message = None
        report.updated_at = datetime.utcnow()
        db.commit()
        logger.info("[%s] Report %s completed", session_id, report_id)
    except Exception as error:
        logger.error("[%s] Report %s failed: %s", session_id, report_id, error, exc_info=True)
        db.rollback()
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            report.current_stage = "Generation failed"
            report.error_message = _public_failure_message(error)
            report.updated_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def _release_report(report_id: int, future: Future) -> None:
    try:
        future.result()
    except Exception:
        logger.exception("Unhandled report worker failure for report %s", report_id)
    finally:
        with _active_lock:
            _active_report_ids.discard(report_id)
        _schedule_next_incomplete_report()


def schedule_report(report_id: int, session_id: str, topic: str) -> bool:
    """Submit a report once; the worker continues across browser navigation."""
    with _active_lock:
        if report_id in _active_report_ids:
            return False
        if len(_active_report_ids) >= max(1, settings.REPORT_MAX_ACTIVE_JOBS):
            raise ReportQueueFullError("The report queue is currently full")
        _active_report_ids.add(report_id)

    try:
        future = _executor.submit(_run_report, session_id, topic, report_id)
    except Exception:
        with _active_lock:
            _active_report_ids.discard(report_id)
        raise
    future.add_done_callback(lambda completed: _release_report(report_id, completed))
    return True


def _schedule_next_incomplete_report() -> None:
    db = SessionLocal()
    try:
        reports = (
            db.query(Report)
            .filter(Report.status.in_(("pending", "generating")))
            .order_by(Report.created_at.asc())
            .all()
        )
        for report in reports:
            try:
                if schedule_report(report.id, report.session_id, report.topic):
                    return
            except ReportQueueFullError:
                return
    finally:
        db.close()


def resume_incomplete_reports() -> int:
    """Resume persisted jobs after an application restart."""
    db = SessionLocal()
    try:
        reports = db.query(Report).filter(Report.status.in_(("pending", "generating"))).all()
        resumed = 0
        for report in reports:
            try:
                resumed += int(schedule_report(report.id, report.session_id, report.topic))
            except ReportQueueFullError:
                break
        return resumed
    finally:
        db.close()


@router.post("/generate", response_model=StatusResponse)
def generate_report(request: ResearchRequest, db: Session = Depends(get_db)):
    session_id = normalize_session_id(request.session_id)
    topic = request.topic.strip()

    existing = (
        db.query(Report)
        .filter(
            Report.session_id == session_id,
            Report.status.in_(("pending", "generating")),
        )
        .order_by(Report.created_at.desc())
        .first()
    )
    if existing:
        schedule_report(existing.id, existing.session_id, existing.topic)
        return StatusResponse(
            status="accepted",
            message="A report is already being generated",
            data={"report_id": existing.id, "resumed": True},
        )

    db_session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not db_session:
        db_session = DBSession(session_id=session_id, topic=topic)
        db.add(db_session)
    else:
        db_session.topic = topic

    report = Report(
        session_id=session_id,
        topic=topic,
        status="pending",
        progress=0,
        current_stage="Queued",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    try:
        schedule_report(report.id, session_id, topic)
    except ReportQueueFullError as error:
        report.status = "failed"
        report.current_stage = "Queue full"
        report.error_message = "The report queue is busy. Wait for a running report and retry."
        db.commit()
        raise HTTPException(status_code=429, detail=str(error)) from error

    return StatusResponse(
        status="accepted",
        message="Report generation started",
        data={"report_id": report.id, "resumed": False},
    )


@router.get("/{session_id}/reports")
def list_reports(session_id: str, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    reports = (
        db.query(Report)
        .filter(Report.session_id == session_id)
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_report(report) for report in reports]


@router.get("/{session_id}/reports/{report_id}")
def get_report(session_id: str, report_id: int, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.session_id == session_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _serialize_report(report)


def _serialize_report(report: Report) -> dict:
    return {
        "id": report.id,
        "session_id": report.session_id,
        "topic": report.topic,
        "status": report.status,
        "progress": report.progress or 0,
        "current_stage": report.current_stage,
        "error_message": report.error_message,
        "executive_summary": report.executive_summary,
        "competitors": json.loads(report.competitors) if report.competitors else None,
        "pricing_insights": json.loads(report.pricing_insights) if report.pricing_insights else None,
        "market_trends": json.loads(report.market_trends) if report.market_trends else None,
        "swot_analysis": json.loads(report.swot_analysis) if report.swot_analysis else None,
        "download_ready": bool(report.status == "done" and report.report_path),
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
