import numpy as np

from backend.services import rag, vector_store


def test_persisted_faiss_index_flows_through_retrieval_pipeline(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_store.settings, "INDEX_DIR", tmp_path)

    def fake_embed_texts(texts):
        return np.array(
            [
                [1.0, 0.0] if "premium pricing" in text else [0.0, 1.0]
                for text in texts
            ],
            dtype="float32",
        )

    monkeypatch.setattr(vector_store, "embed_texts", fake_embed_texts)
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
    monkeypatch.setattr(
        rag,
        "rerank",
        lambda query, candidates, top_k: candidates[:top_k],
    )
    monkeypatch.setattr(rag, "record_retrieval_trace", lambda **kwargs: None)

    store = vector_store.FAISSVectorStore("retrieval-integration")
    store.add_chunks(
        [
            {
                "source": "pricing.pdf",
                "page": 3,
                "chunk_index": 0,
                "text": "The premium pricing tier starts at USD 99 per month.",
            },
            {
                "source": "operations.pdf",
                "page": 1,
                "chunk_index": 0,
                "text": "The support team operates across three regions.",
            },
        ]
    )

    results = rag.retrieve_results(
        session_id="retrieval-integration",
        query="What is the premium pricing tier?",
        top_k=2,
        minimum_score=0.5,
    )

    assert len(results) == 1
    chunk, score = results[0]
    assert chunk["source"] == "pricing.pdf"
    assert chunk["page"] == 3
    assert chunk["_session_id"] == "retrieval-integration"
    assert chunk["_embedding_model"] == "fixture-embedding-model"
    assert score == 1.0
