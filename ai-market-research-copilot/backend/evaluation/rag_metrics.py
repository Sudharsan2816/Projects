from collections.abc import Iterable, Mapping, Sequence
from statistics import mean
from typing import Any


def chunk_identity(chunk: Mapping[str, Any]) -> str:
    """Stable identity for a retrieved chunk used by retrieval evals."""
    if "chunk_id" in chunk:
        return str(chunk["chunk_id"])
    source = chunk.get("source") or chunk.get("filename") or "unknown"
    chunk_index = chunk.get("chunk_index", 0)
    return f"{source}::{chunk_index}"


def recall_at_k(
    retrieved_chunks: Sequence[Mapping[str, Any]],
    relevant_chunk_ids: Iterable[str],
    k: int,
) -> float:
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    retrieved_ids = {chunk_identity(chunk) for chunk in retrieved_chunks[:k]}
    return len(retrieved_ids & relevant) / len(relevant)


def hit_at_k(
    retrieved_chunks: Sequence[Mapping[str, Any]],
    relevant_chunk_ids: Iterable[str],
    k: int,
) -> float:
    return 1.0 if recall_at_k(retrieved_chunks, relevant_chunk_ids, k) > 0 else 0.0


def evaluate_retrieval_case(
    retrieved_chunks: Sequence[Mapping[str, Any]],
    relevant_chunk_ids: Iterable[str],
    k: int = 5,
) -> dict[str, float | int]:
    relevant = set(relevant_chunk_ids)
    retrieved_ids = [chunk_identity(chunk) for chunk in retrieved_chunks[:k]]
    matched = set(retrieved_ids) & relevant
    return {
        "k": k,
        "retrieved": len(retrieved_ids),
        "relevant": len(relevant),
        "matched": len(matched),
        "recall_at_k": recall_at_k(retrieved_chunks, relevant, k),
        "hit_at_k": 1.0 if matched else 0.0,
    }


def summarize_retrieval_suite(case_metrics: Sequence[Mapping[str, float | int]]) -> dict[str, float | int]:
    if not case_metrics:
        return {"cases": 0, "mean_recall_at_k": 0.0, "mean_hit_at_k": 0.0}
    return {
        "cases": len(case_metrics),
        "mean_recall_at_k": mean(float(item["recall_at_k"]) for item in case_metrics),
        "mean_hit_at_k": mean(float(item["hit_at_k"]) for item in case_metrics),
    }
