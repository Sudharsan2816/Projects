"""Deterministic answer-grounding and citation metrics for RAG evaluation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from statistics import mean
from typing import Any

from backend.evaluation.rag_metrics import chunk_identity

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "in", "is", "it", "of", "on", "or", "that", "the", "this",
    "to", "was", "were", "will", "with",
}


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOP_WORDS}


def faithfulness_score(answer: str, contexts: Sequence[str], support_threshold: float = 0.5) -> float:
    """Estimate claim support using content-token coverage against retrieved context.

    This intentionally deterministic heuristic is suitable for regression gates. It is
    not a substitute for a human or model-based factuality review.
    """
    context_tokens = _tokens(" ".join(contexts))
    claims = []
    for sentence in _SENTENCE_RE.split(answer.strip()):
        claim_tokens = _tokens(sentence)
        if len(claim_tokens) >= 3:
            claims.append(claim_tokens)
    if not claims:
        return 0.0
    supported = [
        len(claim & context_tokens) / len(claim) >= support_threshold
        for claim in claims
    ]
    return mean(float(value) for value in supported)


def citation_precision(
    citations: Sequence[Mapping[str, Any]], relevant_chunk_ids: Iterable[str]
) -> float:
    relevant = set(relevant_chunk_ids)
    cited = {chunk_identity(item) for item in citations}
    if not cited:
        return 0.0
    return len(cited & relevant) / len(cited)


def citation_recall(
    citations: Sequence[Mapping[str, Any]], relevant_chunk_ids: Iterable[str]
) -> float:
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    cited = {chunk_identity(item) for item in citations}
    return len(cited & relevant) / len(relevant)


def evaluate_answer_case(
    *,
    answer: str,
    contexts: Sequence[str],
    citations: Sequence[Mapping[str, Any]],
    relevant_chunk_ids: Iterable[str],
) -> dict[str, float]:
    return {
        "faithfulness": faithfulness_score(answer, contexts),
        "citation_precision": citation_precision(citations, relevant_chunk_ids),
        "citation_recall": citation_recall(citations, relevant_chunk_ids),
    }


def summarize_answer_suite(case_metrics: Sequence[Mapping[str, float]]) -> dict[str, float | int]:
    if not case_metrics:
        return {
            "cases": 0,
            "mean_faithfulness": 0.0,
            "mean_citation_precision": 0.0,
            "mean_citation_recall": 0.0,
        }
    return {
        "cases": len(case_metrics),
        "mean_faithfulness": mean(float(item["faithfulness"]) for item in case_metrics),
        "mean_citation_precision": mean(float(item["citation_precision"]) for item in case_metrics),
        "mean_citation_recall": mean(float(item["citation_recall"]) for item in case_metrics),
    }
