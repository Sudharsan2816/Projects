from backend.evaluation.rag_metrics import (
    chunk_identity,
    evaluate_retrieval_case,
    recall_at_k,
    summarize_retrieval_suite,
)


def test_chunk_identity_uses_explicit_chunk_id_when_present():
    assert chunk_identity({"chunk_id": "doc-a::7", "source": "ignored"}) == "doc-a::7"


def test_chunk_identity_falls_back_to_source_and_index():
    assert chunk_identity({"source": "market.pdf", "chunk_index": 2}) == "market.pdf::2"


def test_recall_at_k_scores_relevant_retrieval():
    retrieved = [
        {"source": "market.pdf", "chunk_index": 1},
        {"source": "market.pdf", "chunk_index": 2},
    ]

    assert recall_at_k(retrieved, {"market.pdf::2", "market.pdf::3"}, k=2) == 0.5


def test_evaluate_retrieval_case_returns_hit_and_recall():
    metrics = evaluate_retrieval_case(
        [{"chunk_id": "a"}, {"chunk_id": "b"}],
        {"b", "c"},
        k=2,
    )

    assert metrics["matched"] == 1
    assert metrics["recall_at_k"] == 0.5
    assert metrics["hit_at_k"] == 1.0


def test_summarize_retrieval_suite_averages_metrics():
    summary = summarize_retrieval_suite(
        [
            {"recall_at_k": 1.0, "hit_at_k": 1.0},
            {"recall_at_k": 0.0, "hit_at_k": 0.0},
        ]
    )

    assert summary == {"cases": 2, "mean_recall_at_k": 0.5, "mean_hit_at_k": 0.5}
