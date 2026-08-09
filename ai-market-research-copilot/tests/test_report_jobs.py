import json
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.routes import research
from backend.api.routes.report import download_report
from backend.core.database import SessionLocal, init_db
from backend.models.db_models import Document, Report
from backend.models.db_models import Session as DBSession
from backend.models.schemas import ResearchRequest
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
    db.query(Document).filter(Document.session_id == session_id).delete()
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

    def fake_generate(session, topic, on_progress, source_filenames=None):
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


@pytest.mark.parametrize(
    ("document_count", "expected_scope"),
    [(1, "individual"), (2, "combined")],
)
def test_generate_report_persists_selected_document_scope(
    monkeypatch,
    document_count,
    expected_scope,
):
    init_db()
    session_id = f"selection-{uuid4()}"
    db = SessionLocal()
    db.add(DBSession(session_id=session_id, topic="Selected market"))
    documents = []
    for index in range(document_count):
        document = Document(
            session_id=session_id,
            filename=f"source-{index + 1}.pdf",
            file_type="pdf",
            file_path=f"source-{index + 1}.pdf",
            chunk_count=2,
            indexed=True,
        )
        db.add(document)
        documents.append(document)
    db.commit()
    for document in documents:
        db.refresh(document)

    monkeypatch.setattr(research, "schedule_report", lambda *args: True)
    response = research.generate_report(
        ResearchRequest(
            session_id=session_id,
            topic="Selected market",
            document_ids=[document.id for document in documents],
        ),
        db,
    )

    report = db.query(Report).filter(Report.id == response.data["report_id"]).one()
    assert json.loads(report.source_document_ids) == [
        document.id for document in documents
    ]
    assert json.loads(report.source_document_names) == [
        document.filename for document in documents
    ]
    assert response.data["report_scope"] == expected_scope
    db.close()
    _delete_session(session_id)


def test_generate_report_rejects_an_unavailable_document_selection(monkeypatch):
    init_db()
    session_id = f"selection-{uuid4()}"
    db = SessionLocal()
    db.add(DBSession(session_id=session_id, topic="Selected market"))
    db.commit()
    monkeypatch.setattr(research, "schedule_report", lambda *args: True)

    with pytest.raises(HTTPException) as captured:
        research.generate_report(
            ResearchRequest(
                session_id=session_id,
                topic="Selected market",
                document_ids=[999999],
            ),
            db,
        )

    assert captured.value.status_code == 400
    assert "selected documents are unavailable" in captured.value.detail
    db.close()
    _delete_session(session_id)


def test_report_worker_uses_only_persisted_source_names(monkeypatch, tmp_path):
    session_id, report_id = _create_report()
    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).one()
    report.source_document_ids = json.dumps([11, 12])
    report.source_document_names = json.dumps(["first.pdf", "second.pdf"])
    db.commit()
    db.close()
    data = {
        "executive_summary": "Combined source summary.",
        "competitors": [],
        "pricing_insights": [],
        "market_trends": [],
        "swot_analysis": {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        },
        "data_source": "selected_documents",
    }

    def fake_generate(session, topic, on_progress, source_filenames=None):
        assert source_filenames == ["first.pdf", "second.pdf"]
        return data

    monkeypatch.setattr(research, "generate_full_report", fake_generate)
    monkeypatch.setattr(
        research,
        "generate_pdf_report",
        lambda **kwargs: tmp_path / "selected-report.pdf",
    )

    research._run_report(session_id, "R&D market", report_id)

    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).one()
    assert report.status == "done"
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
