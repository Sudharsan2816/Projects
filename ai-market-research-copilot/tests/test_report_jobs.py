import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.routes import research
from backend.api.routes.report import download_report
from backend.core.database import SessionLocal, init_db
from backend.models.db_models import Report
from backend.models.db_models import Session as DBSession
from backend.services.llm import LLMProviderError
from backend.services.report_generator import generate_pdf_report


def _create_report(status="pending"):
    init_db()
    session_id = f"test-{uuid4()}"
    db = SessionLocal()
    db.add(DBSession(session_id=session_id, topic="R&D market"))
    report = Report(session_id=session_id, topic="R&D market", status=status, progress=0)
    db.add(report)
    db.commit()
    db.refresh(report)
    report_id = report.id
    db.close()
    return session_id, report_id


def _delete_session(session_id):
    db = SessionLocal()
    db.query(Report).filter(Report.session_id == session_id).delete()
    db.query(DBSession).filter(DBSession.session_id == session_id).delete()
    db.commit()
    db.close()


def test_report_worker_persists_completion_without_browser_request(monkeypatch, tmp_path):
    session_id, report_id = _create_report()
    data = {
        "executive_summary": "R&D is growing.",
        "competitors": [{"name": "A&B"}],
        "pricing_insights": [],
        "market_trends": [],
        "swot_analysis": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        "data_source": "web_search+llm",
    }

    def fake_generate(session, topic, on_progress):
        on_progress(42, "Competitor analysis complete")
        return data

    monkeypatch.setattr(research, "generate_full_report", fake_generate)
    monkeypatch.setattr(research, "generate_pdf_report", lambda **kwargs: tmp_path / "report.pdf")

    research._run_report(session_id, "R&D market", report_id)

    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).one()
    assert report.status == "done"
    assert report.progress == 100
    assert report.current_stage == "Report ready"
    assert json.loads(report.competitors)[0]["name"] == "A&B"
    db.close()
    _delete_session(session_id)


def test_report_worker_persists_safe_provider_failure(monkeypatch):
    session_id, report_id = _create_report()

    def fail_report(*args, **kwargs):
        raise LLMProviderError({"nvidia": "authorization failed", "gemini": "quota exhausted"})

    monkeypatch.setattr(research, "generate_full_report", fail_report)
    research._run_report(session_id, "R&D market", report_id)

    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).one()
    assert report.status == "failed"
    assert "authorization failed" in report.error_message
    assert "quota exhausted" in report.error_message
    db.close()
    _delete_session(session_id)


def test_pdf_generator_handles_market_symbols(monkeypatch, tmp_path):
    from backend.services import report_generator

    monkeypatch.setattr(report_generator.settings, "REPORTS_DIR", tmp_path)
    output = generate_pdf_report(
        "symbol-test",
        "R&D tools below <5%",
        "A&B spending is <5% and rising.",
        [{"name": "A&B", "description": "R&D", "market_position": "Leader"}],
        [],
        [],
        {"strengths": ["R&D"], "weaknesses": [], "opportunities": [], "threats": []},
    )

    assert output.is_file()
    assert output.stat().st_size > 0


def test_report_download_rejects_files_outside_reports_directory(tmp_path):
    session_id, report_id = _create_report(status="done")
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"not a report")
    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).one()
    report.report_path = str(outside)
    db.commit()

    with pytest.raises(HTTPException) as captured:
        download_report(session_id, report_id, db)

    assert captured.value.status_code == 404
    db.close()
    _delete_session(session_id)
