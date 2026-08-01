from backend.evaluation.answer_metrics import (
    citation_precision,
    citation_recall,
    evaluate_answer_case,
    faithfulness_score,
    summarize_answer_suite,
)


def test_faithfulness_scores_supported_claims():
    answer = "The market reaches USD 1.2 billion by 2030. Growth is near 22 percent."
    contexts = [
        "The market is projected to reach USD 1.2 billion by 2030 with growth near 22 percent."
    ]

    assert faithfulness_score(answer, contexts) == 1.0


def test_faithfulness_penalizes_unsupported_claims():
    answer = "The market reaches USD 1.2 billion by 2030. The product is free forever."
    contexts = ["The market is projected to reach USD 1.2 billion by 2030."]

    assert faithfulness_score(answer, contexts) == 0.5


def test_citation_metrics_use_chunk_identity():
    citations = [{"source": "market.pdf", "chunk_index": 1}, {"chunk_id": "wrong"}]
    relevant = {"market.pdf::1", "market.pdf::2"}

    assert citation_precision(citations, relevant) == 0.5
    assert citation_recall(citations, relevant) == 0.5


def test_answer_case_and_suite_summary():
    case = evaluate_answer_case(
        answer="Buyers prioritize transcript accuracy and retention controls.",
        contexts=["Buyers prioritize transcript accuracy and data retention controls."],
        citations=[{"chunk_id": "buyers::0"}],
        relevant_chunk_ids=["buyers::0"],
    )
    summary = summarize_answer_suite([case])

    assert case == {
        "faithfulness": 1.0,
        "citation_precision": 1.0,
        "citation_recall": 1.0,
    }
    assert summary["cases"] == 1
    assert summary["mean_faithfulness"] == 1.0
