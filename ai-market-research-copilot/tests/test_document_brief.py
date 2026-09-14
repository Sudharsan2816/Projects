import asyncio
from uuid import uuid4

import pytest

from backend.api.routes import upload
from backend.core.database import SessionLocal, init_db
from backend.models.db_models import Document
from backend.models.db_models import Session as DBSession
from backend.services import document_brief


def test_document_brief_uses_bounded_source_context(monkeypatch):
    chunks = [
        {"text": f"Section {index} market evidence " + ("data " * 500), "page": index + 1}
        for index in range(20)
    ]
    captured = {}

    def fake_generate(prompt, system):
        captured["prompt"] = prompt
        captured["system"] = system
        return """Overview
The source reviews the market.

Key findings
- Demand is discussed.

Important figures
- No material figures found in the sampled text.

Research gaps
- Customer segmentation is not covered."""

    monkeypatch.setattr(document_brief, "generate", fake_generate)

    result = document_brief.build_document_brief("market.txt", chunks)

    assert result.startswith("Overview")
    assert "Use only the supplied document excerpts" in captured["system"]
    assert "Section 0 market evidence" in captured["prompt"]
    assert "Section 19 market evidence" in captured["prompt"]
    assert len(captured["prompt"]) < document_brief.MAX_BRIEF_CONTEXT_CHARS + 2_000


def test_document_brief_rejects_empty_documents():
    with pytest.raises(ValueError, match="no text"):
        document_brief.build_document_brief("empty.txt", [])


def test_existing_document_brief_is_generated_and_persisted(monkeypatch, tmp_path):
    init_db()
    session_id = f"brief-{uuid4()}"
    source = tmp_path / "market.txt"
    source.write_text("The market is worth USD 120 million and is growing 18% annually.")

    db = SessionLocal()
    db.add(DBSession(session_id=session_id))
    doc = Document(
        session_id=session_id,
        filename=source.name,
        file_type="txt",
        file_path=str(source),
        file_size_kb=1,
        chunk_count=1,
        indexed=True,
        brief_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    expected = "Overview\nA concise market source.\n\nKey findings\n- Growth is reported."
    monkeypatch.setattr(upload, "build_document_brief", lambda filename, chunks: expected)

    response = asyncio.run(upload.generate_document_brief(session_id, doc.id, db))

    db.refresh(doc)
    assert response.brief_status == "ready"
    assert response.brief == expected
    assert doc.brief == expected
    assert doc.brief_status == "ready"

    db.query(Document).filter(Document.session_id == session_id).delete()
    db.query(DBSession).filter(DBSession.session_id == session_id).delete()
    db.commit()
    db.close()
