"""Run the committed RAG retrieval and answer-grounding evaluation suite."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.evaluation.answer_metrics import evaluate_answer_case, summarize_answer_suite
from backend.evaluation.rag_metrics import evaluate_retrieval_case, summarize_retrieval_suite
from backend.services.embedder import embed_query, embed_texts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "evals" / "rag_eval_dataset.json"
DEFAULT_JSON = PROJECT_ROOT / "evals" / "rag_eval_results.json"
DEFAULT_MARKDOWN = PROJECT_ROOT / "docs" / "RAG_EVALUATION.md"


def _retrieve(corpus: list[dict[str, Any]], query: str, top_k: int) -> list[dict[str, Any]]:
    embeddings = embed_texts([item["text"] for item in corpus])
    query_embedding = embed_query(query)
    scores = embeddings @ query_embedding
    ranked = np.argsort(scores)[::-1][:top_k]
    return [dict(corpus[index], score=float(scores[index])) for index in ranked]


def run_evaluation(dataset_path: Path, top_k: int) -> dict[str, Any]:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    corpus = dataset["corpus"]
    cases = []
    retrieval_metrics = []
    answer_metrics = []

    for case in dataset["cases"]:
        retrieved = _retrieve(corpus, case["question"], top_k)
        retrieval = evaluate_retrieval_case(retrieved, case["relevant_chunk_ids"], top_k)
        answer = evaluate_answer_case(
            answer=case["reference_answer"],
            contexts=[item["text"] for item in retrieved],
            citations=case["citations"],
            relevant_chunk_ids=case["relevant_chunk_ids"],
        )
        retrieval_metrics.append(retrieval)
        answer_metrics.append(answer)
        cases.append(
            {
                "id": case["id"],
                "question": case["question"],
                "retrieved_chunk_ids": [item["chunk_id"] for item in retrieved],
                "retrieval": retrieval,
                "answer": answer,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_path.name,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "top_k": top_k,
        "retrieval_summary": summarize_retrieval_suite(retrieval_metrics),
        "answer_summary": summarize_answer_suite(answer_metrics),
        "cases": cases,
        "methodology": {
            "retrieval": "Cosine similarity over the production local embedding model.",
            "faithfulness": "Deterministic claim-token support heuristic over retrieved contexts.",
            "citations": "Exact relevant chunk identity precision and recall.",
        },
    }


def render_markdown(results: dict[str, Any]) -> str:
    retrieval = results["retrieval_summary"]
    answer = results["answer_summary"]
    rows = []
    for case in results["cases"]:
        rows.append(
            "| {id} | {recall:.2f} | {hit:.2f} | {faith:.2f} | {precision:.2f} | {citation_recall:.2f} |".format(
                id=case["id"],
                recall=case["retrieval"]["recall_at_k"],
                hit=case["retrieval"]["hit_at_k"],
                faith=case["answer"]["faithfulness"],
                precision=case["answer"]["citation_precision"],
                citation_recall=case["answer"]["citation_recall"],
            )
        )
    return "\n".join(
        [
            "# RAG Evaluation Report",
            "",
            f"Generated: {results['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Cases: {retrieval['cases']}",
            f"- Mean recall@{results['top_k']}: {retrieval['mean_recall_at_k']:.3f}",
            f"- Mean hit@{results['top_k']}: {retrieval['mean_hit_at_k']:.3f}",
            f"- Mean deterministic faithfulness: {answer['mean_faithfulness']:.3f}",
            f"- Mean citation precision: {answer['mean_citation_precision']:.3f}",
            f"- Mean citation recall: {answer['mean_citation_recall']:.3f}",
            "",
            "## Cases",
            "",
            "| Case | Recall | Hit | Faithfulness | Citation precision | Citation recall |",
            "|---|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "## Methodology and limitations",
            "",
            "Retrieval uses the same local sentence-transformer family as the application and a labeled fixture corpus. "
            "The answer-level faithfulness score is a deterministic regression heuristic based on claim-token support; "
            "it does not replace human review or an independent model judge. Citation metrics use exact chunk IDs. "
            "Production evaluations should add real uploaded documents, adversarial questions, and provider-generated answers.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--check-thresholds", action="store_true")
    args = parser.parse_args()

    results = run_evaluation(args.dataset, args.top_k)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    args.output_markdown.write_text(render_markdown(results), encoding="utf-8")

    if args.check_thresholds:
        retrieval = results["retrieval_summary"]
        answer = results["answer_summary"]
        if (
            retrieval["mean_hit_at_k"] < 1.0
            or retrieval["mean_recall_at_k"] < 0.8
            or answer["mean_faithfulness"] < 0.8
            or answer["mean_citation_precision"] < 0.8
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
