import json

import numpy as np
import pytest

from backend.api.routes import upload
from backend.services import vector_store


class EmptyQuery:
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None


class EmptyDatabase:
    def query(self, *args, **kwargs):
        return EmptyQuery()


def _configure_fake_embeddings(monkeypatch, index_dir):
    monkeypatch.setattr(vector_store.settings, "INDEX_DIR", index_dir)
    monkeypatch.setattr(
        vector_store,
        "embed_texts",
        lambda texts: np.array([[1.0, 0.0] for _text in texts], dtype="float32"),
    )
    monkeypatch.setattr(
        vector_store,
        "embed_query",
        lambda query: np.array([1.0, 0.0], dtype="float32"),
    )
    monkeypatch.setattr(
        vector_store,
        "get_last_embedding_model",
        lambda: "fixture-embedding-model",
    )


def _chunk(source, text):
    return {
        "source": source,
        "page": 1,
        "chunk_index": 0,
        "text": text,
    }


def test_query_loads_only_the_current_sessions_index(monkeypatch, tmp_path):
    _configure_fake_embeddings(monkeypatch, tmp_path)

    old_store = vector_store.FAISSVectorStore("old-session")
    old_store.add_chunks([_chunk("krishikube.pdf", "Old KrishiKube research")])

    current_store = vector_store.FAISSVectorStore("current-session")
    current_store.add_chunks(
        [
            _chunk("new-market-one.pdf", "Current market evidence one"),
            _chunk("new-market-two.pdf", "Current market evidence two"),
        ]
    )

    results = vector_store.FAISSVectorStore("current-session").search(
        "current market",
        top_k=10,
    )

    assert old_store.index_path != current_store.index_path
    assert current_store.total_vectors() == 2
    assert {chunk["source"] for chunk, _score in results} == {
        "new-market-one.pdf",
        "new-market-two.pdf",
    }
    assert all(chunk["_session_id"] == "current-session" for chunk, _score in results)


def test_reset_removes_only_the_selected_sessions_data(monkeypatch, tmp_path):
    index_dir = tmp_path / "indexes"
    upload_dir = tmp_path / "uploads"
    index_dir.mkdir()
    upload_dir.mkdir()
    _configure_fake_embeddings(monkeypatch, index_dir)
    monkeypatch.setattr(upload.settings, "INDEX_DIR", index_dir)
    monkeypatch.setattr(upload.settings, "UPLOAD_DIR", upload_dir)

    target_store = vector_store.FAISSVectorStore("target-session")
    target_store.add_chunks([_chunk("old.pdf", "Old target content")])
    other_store = vector_store.FAISSVectorStore("other-session")
    other_store.add_chunks([_chunk("other.pdf", "Other session content")])

    target_upload_dir = upload_dir / "target-session"
    target_upload_dir.mkdir()
    (target_upload_dir / "old.pdf").write_text("old", encoding="utf-8")

    upload._reset_session_data("target-session", EmptyDatabase())

    assert not target_store.index_path.exists()
    assert not target_store.meta_path.exists()
    assert not target_upload_dir.exists()
    assert other_store.index_path.exists()
    assert other_store.meta_path.exists()


def test_foreign_session_metadata_is_rejected(monkeypatch, tmp_path):
    _configure_fake_embeddings(monkeypatch, tmp_path)
    store = vector_store.FAISSVectorStore("current-session")
    store.add_chunks([_chunk("current.pdf", "Current content")])

    metadata = json.loads(store.meta_path.read_text(encoding="utf-8"))
    metadata[0]["_session_id"] = "foreign-session"
    store.meta_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(RuntimeError, match="foreign session ids"):
        vector_store.FAISSVectorStore("current-session").search("query")
