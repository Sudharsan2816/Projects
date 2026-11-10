"""Measure what the NIM reranker adds over plain embedding order.

Run from ai-market-research-copilot/ with NVIDIA_API_KEY set:

    python scripts/rerank_ablation.py
    python scripts/rerank_ablation.py --dataset path/to/labelled_set.json

The dataset uses the format of evals/rag_eval_dataset.json: a "corpus" of chunks
(each with "chunk_id" and "text") and "cases" (each with "id", "question" and
"relevant_chunk_ids"). For each question, the top candidates by cosine similarity
are scored twice: in embedding order, and after the production rerank() call.
No relevance threshold is applied, so the comparison isolates reranking.

The script stops if the reranker silently falls back to embedding order, so a
missing key or a failing endpoint can never be reported as "no lift".
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

from backend.core.config import get_settings
from backend.evaluation.rag_metrics import chunk_identity, recall_at_k
from backend.services.embedder import embed_query, embed_texts
from backend.services.llm import rerank

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "evals" / "rag_eval_dataset.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evals" / "rerank_ablation_results.json"
CUTOFFS = (1, 3, 6)


def first_relevant_rank(ranked: list[dict[str, Any]], relevant: set[str]) -> int | None:
    for position, chunk in enumerate(ranked, start=1):
        if chunk_identity(chunk) in relevant:
            return position
    return None


def score_ranking(ranked: list[dict[str, Any]], relevant: set[str]) -> dict[str, Any]:
    rank = first_relevant_rank(ranked, relevant)
    scores: dict[str, Any] = {"first_relevant_rank": rank, "reciprocal_rank": 1.0 / rank if rank else 0.0}
    for k in CUTOFFS:
        recall = recall_at_k(ranked, relevant, k)
        scores[f"hit@{k}"] = 1.0 if recall > 0 else 0.0
        scores[f"complete_hit@{k}"] = 1.0 if recall == 1.0 else 0.0
        scores[f"recall@{k}"] = recall
    return scores


def summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    keys = [key for key in rows[0] if key != "first_relevant_rank"]
    summary = {("mrr" if key == "reciprocal_rank" else key): round(mean(row[key] for row in rows), 4) for key in keys}
    return summary


def run(dataset_path: Path, fetch_k: int) -> dict[str, Any]:
    settings = get_settings()
    if not settings.NVIDIA_API_KEY:
        raise SystemExit("NVIDIA_API_KEY is not set, so rerank() would return embedding order unchanged.")

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    corpus = dataset["corpus"]
    embeddings = embed_texts([chunk["text"] for chunk in corpus])
    fetch_k = min(fetch_k, len(corpus))

    cases, baseline_rows, reranked_rows = [], [], []
    for case in dataset["cases"]:
        relevant = set(case["relevant_chunk_ids"])
        scores = embeddings @ embed_query(case["question"])
        order = np.argsort(scores)[::-1][:fetch_k]
        candidates = [(corpus[i], float(scores[i])) for i in order]

        reranked_pairs = rerank(case["question"], candidates, top_k=fetch_k)
        if [score for _, score in reranked_pairs] == [score for _, score in candidates[: len(reranked_pairs)]]:
            raise SystemExit(
                f"The reranker returned embedding order unchanged for case {case['id']!r}; "
                "the endpoint probably failed. Check the warning above and retry."
            )

        baseline = score_ranking([chunk for chunk, _ in candidates], relevant)
        reranked = score_ranking([chunk for chunk, _ in reranked_pairs], relevant)
        baseline_rows.append(baseline)
        reranked_rows.append(reranked)
        cases.append(
            {
                "id": case["id"],
                "question": case["question"],
                "relevant_chunk_ids": sorted(relevant),
                "embedding_order": [chunk_identity(chunk) for chunk, _ in candidates],
                "reranked_order": [chunk_identity(chunk) for chunk, _ in reranked_pairs],
                "first_relevant_rank": {"embedding": baseline["first_relevant_rank"], "reranked": reranked["first_relevant_rank"]},
            }
        )

    base, rr = summarize(baseline_rows), summarize(reranked_rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.name),
        "cases": len(cases),
        "corpus_chunks": len(corpus),
        "fetch_k": fetch_k,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.NVIDIA_EMBEDDING_MODEL if settings.EMBEDDING_PROVIDER == "nvidia" else settings.EMBEDDING_MODEL,
        "reranker_model": settings.NVIDIA_RERANKER_MODEL,
        "embedding_order": base,
        "reranked": rr,
        "difference": {key: round(rr[key] - base[key], 4) for key in base},
        "helped": [c["id"] for c, b, r in zip(cases, baseline_rows, reranked_rows) if r["reciprocal_rank"] > b["reciprocal_rank"]],
        "hurt": [c["id"] for c, b, r in zip(cases, baseline_rows, reranked_rows) if r["reciprocal_rank"] < b["reciprocal_rank"]],
        "case_results": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--fetch-k", type=int, default=get_settings().RERANKER_FETCH_K)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    results = run(args.dataset, args.fetch_k)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"{results['cases']} questions, {results['corpus_chunks']} chunks, top {results['fetch_k']} candidates")
    print(f"{'metric':<16}{'embedding':>11}{'reranked':>10}{'change':>9}")
    for key, value in results["embedding_order"].items():
        print(f"{key:<16}{value:>11.4f}{results['reranked'][key]:>10.4f}{results['difference'][key]:>+9.4f}")
    print(f"reranking moved the first relevant chunk up for {len(results['helped'])} question(s) and down for {len(results['hurt'])}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
