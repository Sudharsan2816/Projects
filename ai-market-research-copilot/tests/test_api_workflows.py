import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.routes import chat as chat_routes
from backend.api.routes import upload as upload_routes
from backend.core import database
from backend.core.database import Base, get_db
from backend.models.db_models import Session as DBSession


def _database_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api-test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _test_app(router, session_factory):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app


def test_upload_api_indexes_and_lists_a_document(monkeypatch, tmp_path):
    session_factory = _database_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(upload_routes.settings, "UPLOAD_DIR", upload_dir)

    class FakeVectorStore:
        def __init__(self, session_id):
            self.session_id = session_id
            self.metadata = []

        def add_chunks(self, chunks):
            self.metadata.extend(chunks)
            return len(chunks)

    monkeypatch.setattr(upload_routes, "FAISSVectorStore", FakeVectorStore)
    monkeypatch.setattr(
        upload_routes,
        "parse_document",
        lambda path: [{"source": path.name, "page": 1, "text": path.read_text()}],
    )
    monkeypatch.setattr(
        upload_routes,
        "chunk_pages",
        lambda pages: [
            {
                "source": pages[0]["source"],
                "page": 1,
                "chunk_index": 0,
                "text": pages[0]["text"],
            }
        ],
    )
    monkeypatch.setattr(
        upload_routes,
        "build_document_brief",
        lambda filename, chunks: f"Brief for {filename}: {chunks[0]['text']}",
    )

    app = _test_app(upload_routes.router, session_factory)
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/upload/",
            data={"session_id": "integration-session"},
            files={"file": ("market.txt", b"Demand grew 18 percent.", "text/plain")},
        )
        documents_response = client.get(
            "/api/v1/upload/integration-session/documents"
        )

    assert upload_response.status_code == 200
    uploaded = upload_response.json()
    assert uploaded["session_id"] == "integration-session"
    assert uploaded["filename"] == "market.txt"
    assert uploaded["chunk_count"] == 1
    assert uploaded["brief_status"] == "ready"
    assert "Demand grew 18 percent" in uploaded["brief"]
    assert (upload_dir / "integration-session" / "market.txt").read_text() == (
        "Demand grew 18 percent."
    )

    assert documents_response.status_code == 200
    documents = documents_response.json()
    assert len(documents) == 1
    assert documents[0]["filename"] == "market.txt"
    assert documents[0]["indexed"] is True


def test_streaming_chat_api_emits_sse_and_persists_history(monkeypatch, tmp_path):
    session_factory = _database_factory(tmp_path)
    db = session_factory()
    db.add(DBSession(session_id="stream-session"))
    db.commit()
    db.close()

    source = {
        "filename": "market.txt",
        "chunk_index": 0,
        "excerpt": "Demand grew 18 percent.",
        "relevance_score": 0.93,
    }

    def fake_chat_stream(**kwargs):
        assert kwargs["session_id"] == "stream-session"
        assert kwargs["user_message"] == "What changed?"
        yield "Demand ", None, None
        yield "grew 18 percent.", None, None
        yield None, [source], "documents"

    monkeypatch.setattr(chat_routes, "chat_stream", fake_chat_stream)
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    app = _test_app(chat_routes.router, session_factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/stream",
            json={"session_id": "stream-session", "message": "What changed?"},
        )
        history_response = client.get("/api/v1/chat/stream-session/history")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert [event["token"] for event in events if "token" in event] == [
        "Demand ",
        "grew 18 percent.",
    ]
    assert events[-1] == {
        "done": True,
        "sources": [source],
        "answer_mode": "documents",
    }

    assert history_response.status_code == 200
    history = history_response.json()
    assert [(message["role"], message["content"]) for message in history] == [
        ("user", "What changed?"),
        ("assistant", "Demand grew 18 percent."),
    ]
    assert history[-1]["sources"] == [source]
    assert history[-1]["answer_mode"] == "documents"
