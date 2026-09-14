from types import SimpleNamespace

import numpy as np

from backend.services import embedder, rag, vector_store


class RecordingLogger:
    def __init__(self):
        self.debug_events = []
        self.warning_events = []

    def debug(self, message, *args, extra=None, **kwargs):
        self.debug_events.append((message, extra or {}))

    def warning(self, message, *args, extra=None, **kwargs):
        self.warning_events.append((message, extra or {}))

    def info(self, message, *args, **kwargs):
        return None


def test_embed_query_records_the_model_that_succeeded(monkeypatch):
    token = embedder._last_embedding_model.set(None)
    try:
        monkeypatch.setattr(embedder.settings, "EMBEDDING_PROVIDER", "nvidia")
        monkeypatch.setattr(embedder.settings, "NVIDIA_API_KEY", "test-key")
        monkeypatch.setattr(embedder.settings, "NVIDIA_EMBEDDING_MODEL", "test-model")
        monkeypatch.setattr(
            embedder,
            "_nvidia_embed",
            lambda texts, input_type: np.array([[1.0, 0.0]], dtype="float32"),
        )

        result = embedder.embed_query("exact test query")

        assert result.tolist() == [1.0, 0.0]
        assert embedder.get_last_embedding_model() == "test-model"
    finally:
        embedder._last_embedding_model.reset(token)


def test_vector_store_persists_and_checks_embedding_model(monkeypatch, tmp_path):
    recorded = RecordingLogger()
    store = vector_store.FAISSVectorStore("debug-model-test")
    store.index_path = tmp_path / "debug-model-test.faiss"
    store.meta_path = tmp_path / "debug-model-test.meta"

    monkeypatch.setattr(vector_store.settings, "DEBUG", True)
    monkeypatch.setattr(vector_store, "logger", recorded)
    monkeypatch.setattr(
        vector_store,
        "embed_texts",
        lambda texts: np.array([[1.0, 0.0]], dtype="float32"),
    )
    monkeypatch.setattr(
        vector_store,
        "embed_query",
        lambda query: np.array([1.0, 0.0], dtype="float32"),
    )
    monkeypatch.setattr(
        vector_store,
        "get_last_embedding_model",
        lambda: "test-embedding-model",
    )

    store.add_chunks(
        [
            {
                "source": "report.pdf",
                "page": 1,
                "chunk_index": 0,
                "text": "A market research chunk.",
            }
        ]
    )
    results = store.search("exact test query", top_k=1)

    assert results[0][0]["_embedding_model"] == "test-embedding-model"
    model_event = next(
        extra for message, extra in recorded.debug_events if message == "query_embedding_model"
    )
    assert model_event["query"] == "exact test query"
    assert model_event["query_embedding_model"] == "test-embedding-model"
    assert model_event["ingestion_embedding_models"] == ["test-embedding-model"]
    assert recorded.warning_events == []


def test_retrieval_logs_faiss_threshold_and_reranked_chunks(monkeypatch):
    chunks = [
        {
            "source": "market.pdf",
            "page": 1,
            "chunk_index": 0,
            "text": "Relevant market size evidence " * 10,
        },
        {
            "source": "other.pdf",
            "page": 2,
            "chunk_index": 0,
            "text": "Weakly related evidence.",
        },
    ]

    class FakeStore:
        def __init__(self, session_id):
            self.session_id = session_id
            self.metadata = chunks
            self.index = SimpleNamespace(ntotal=len(chunks))

        def search(self, query, top_k=None, source_filenames=None):
            return [(chunks[0], 0.81), (chunks[1], 0.22)]

    recorded = RecordingLogger()
    monkeypatch.setattr(rag.settings, "DEBUG", True)
    monkeypatch.setattr(rag, "logger", recorded)
    monkeypatch.setattr(rag, "FAISSVectorStore", FakeStore)
    monkeypatch.setattr(
        rag,
        "rerank",
        lambda query, candidates, top_k: [(candidates[0][0], 3.4)],
    )
    monkeypatch.setattr(rag, "record_retrieval_trace", lambda **kwargs: None)

    results = rag.retrieve_results(
        "debug-session",
        "exact retrieval query",
        top_k=1,
        minimum_score=0.35,
    )

    assert results == [(chunks[0], 3.4)]
    faiss_event = next(
        extra for message, extra in recorded.debug_events if message == "retrieval_after_faiss"
    )
    assert faiss_event["query"] == "exact retrieval query"
    assert faiss_event["faiss_returned"] == 2
    assert faiss_event["threshold_cleared"] == 1
    assert len(faiss_event["chunks"][0]["snippet"]) == 150
    assert faiss_event["chunks"][0]["score"] == 0.81

    rerank_event = next(
        extra for message, extra in recorded.debug_events if message == "retrieval_after_rerank"
    )
    assert rerank_event["rerank_input_count"] == 1
    assert rerank_event["rerank_returned"] == 1
    assert rerank_event["chunks"][0]["score"] == 3.4


def test_source_diversification_round_robins_ranked_sources():
    candidates = [
        ({"source": "alpha.pdf", "text": "alpha one"}, 0.9),
        ({"source": "alpha.pdf", "text": "alpha two"}, 0.8),
        ({"source": "beta.pdf", "text": "beta one"}, 0.7),
        ({"source": "beta.pdf", "text": "beta two"}, 0.6),
    ]

    diversified = vector_store._source_diverse_results(candidates, limit=4)

    assert [chunk["text"] for chunk, _score in diversified] == [
        "alpha one",
        "beta one",
        "alpha two",
        "beta two",
    ]
