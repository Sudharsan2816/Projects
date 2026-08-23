import re
from difflib import SequenceMatcher
from time import perf_counter
from typing import Any, Dict, List, Tuple

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.observability import record_retrieval_trace

from .llm import generate, rerank
from .vector_store import FAISSVectorStore

logger = get_logger(__name__)
settings = get_settings()

NO_DOCUMENT_CONTEXT = (
    "No indexed document context was found for this question. "
    "Upload relevant source documents or ask about content already indexed in this session."
)
NOT_COVERED_RESPONSE = "Not covered in the uploaded documents."

_LEXICAL_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "about",
    "be",
    "by",
    "can",
    "could",
    "describe",
    "details",
    "did",
    "do",
    "does",
    "explain",
    "for",
    "from",
    "give",
    "have",
    "how",
    "in",
    "information",
    "is",
    "it",
    "know",
    "me",
    "of",
    "on",
    "overview",
    "please",
    "provide",
    "s",
    "say",
    "summary",
    "tell",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "would",
    "you",
}


def _normalize_lexical_token(token: str) -> str:
    comparative_forms = {
        "better": "good",
        "cheaper": "cheap",
        "higher": "high",
        "lower": "low",
        "stronger": "strong",
        "weaker": "weak",
        "worse": "bad",
    }
    if token in comparative_forms:
        return comparative_forms[token]
    if token in {"founder", "founded", "founding"}:
        return "found"
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _lexical_terms(text: str) -> set[str]:
    return {
        _normalize_lexical_token(token)
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in _LEXICAL_STOP_WORDS
    }


def _document_entity_vocabulary(session_id: str) -> dict[str, str]:
    """Return canonical, report-backed spellings for likely named entities."""
    store = FAISSVectorStore(session_id)
    store.total_vectors()
    vocabulary: dict[str, str] = {}
    for chunk in store.metadata:
        text = str(chunk.get("text", ""))
        for token in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,}\b", text):
            normalized = token.lower()
            if normalized in _LEXICAL_STOP_WORDS or not token[0].isupper():
                continue
            existing = vocabulary.get(normalized)
            if existing is None or sum(char.isupper() for char in token) > sum(
                char.isupper() for char in existing
            ):
                vocabulary[normalized] = token
    return vocabulary


def correct_document_entity_typos(session_id: str, query: str) -> str:
    """Correct only high-confidence named-entity typos backed by this session's index."""
    vocabulary = _document_entity_vocabulary(session_id)
    if not vocabulary:
        return query

    replacements: dict[str, str] = {}
    for token in re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,}\b", query):
        normalized = token.lower()
        exact = vocabulary.get(normalized)
        if exact:
            # Preserve normal prose, but restore canonical mixed-case brand spellings.
            if any(char.isupper() for char in exact[1:]):
                replacements[token] = exact
            continue
        if len(token) < 7 or not token[0].isupper() or normalized in _LEXICAL_STOP_WORDS:
            continue

        ranked = sorted(
            (
                (SequenceMatcher(None, normalized, candidate).ratio(), candidate)
                for candidate in vocabulary
                if abs(len(candidate) - len(normalized)) <= 2
            ),
            reverse=True,
        )
        if not ranked or ranked[0][0] < 0.9:
            continue
        if len(ranked) > 1 and ranked[0][0] - ranked[1][0] < 0.06:
            continue
        replacements[token] = vocabulary[ranked[0][1]]

    corrected = query
    for original, replacement in replacements.items():
        corrected = re.sub(rf"\b{re.escape(original)}\b", replacement, corrected)
    if corrected != query:
        logger.info(
            "DOCUMENT_QUERY_ENTITY_CORRECTION session_id=%s original=%r corrected=%r",
            session_id,
            query,
            corrected,
        )
    return corrected


def find_document_entity_mention(session_id: str, text: str) -> str | None:
    """Find one unambiguous session-backed entity in earlier conversation text."""
    vocabulary = _document_entity_vocabulary(session_id)
    if not vocabulary:
        return None
    corrected = correct_document_entity_typos(session_id, text)
    mentioned = {
        canonical
        for normalized, canonical in vocabulary.items()
        if re.search(rf"\b{re.escape(normalized)}\b", corrected, flags=re.IGNORECASE)
    }
    if not mentioned:
        return None

    # Mixed-case brand names are more specific than ordinary title-cased report words.
    mixed_case = {
        candidate
        for candidate in mentioned
        if any(char.isupper() for char in candidate[1:])
    }
    candidates = mixed_case or mentioned
    if len(candidates) != 1:
        return None
    return next(iter(candidates))


def _lexical_results(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Tuple[Dict[str, Any], float]]:
    """Recover exact report facts that dense similarity can under-score."""
    query_terms = _lexical_terms(query)
    if not query_terms:
        return []

    minimum_matches = 1 if len(query_terms) == 1 else 2
    matches: List[Tuple[Dict[str, Any], float]] = []
    for chunk in chunks:
        overlap = query_terms.intersection(_lexical_terms(str(chunk.get("text", ""))))
        if len(overlap) < minimum_matches:
            continue
        coverage = len(overlap) / len(query_terms)
        matches.append((chunk, coverage))
    return sorted(matches, key=lambda item: item[1], reverse=True)[:top_k]


def _chunk_key(chunk: Dict[str, Any]) -> tuple[Any, ...]:
    return (
        chunk.get("source"),
        chunk.get("page"),
        chunk.get("chunk_index"),
        chunk.get("text"),
    )


_COMPARATIVE_QUERY_PATTERN = re.compile(
    r"\b(?:compare|comparison|versus|vs\.?|stronger|weaker|better|worse|"
    r"cheaper|costlier|higher|lower|which (?:one|company|product|brand))\b",
    flags=re.IGNORECASE,
)


def _is_comparative_query(query: str) -> bool:
    return bool(_COMPARATIVE_QUERY_PATTERN.search(query))


def has_indexed_documents(
    session_id: str,
    source_filenames: List[str] | None = None,
) -> bool:
    return FAISSVectorStore(session_id).total_vectors(source_filenames) > 0


def _normalize_context_text(text: str) -> str:
    """Repair the common PDF-extraction artifact where ₹ is emitted as I before a number."""
    return re.sub(r"\bI(?=\d[\d,]*(?:\.\d+)?)", "₹", text)


def build_context(
    results: List[Tuple[Dict[str, Any], float]], max_chars: int = 6000
) -> str:
    """Concatenate retrieved chunks into a context string with citations."""
    parts = []
    total = 0
    for chunk, _score in results:
        chunk_text = _normalize_context_text(str(chunk["text"]))
        snippet = f"[Source: {chunk['source']}, Page {chunk.get('page', '?')}]\n{chunk_text}"
        if total + len(snippet) > max_chars:
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n\n---\n\n".join(parts)


def _retrieval_debug_chunks(
    results: List[Tuple[Dict[str, Any], float]],
) -> List[Dict[str, Any]]:
    """Build a compact, structured representation for retrieval debugging."""
    return [
        {
            "source_filename": chunk.get("source", "unknown"),
            "page": chunk.get("page"),
            "chunk_index": chunk.get("chunk_index"),
            "snippet": re.sub(r"\s+", " ", str(chunk.get("text", ""))).strip()[:150],
            "score": round(float(score), 6),
        }
        for chunk, score in results
    ]


def retrieve_results(
    session_id: str,
    query: str,
    top_k: int | None = None,
    minimum_score: float | None = None,
    diagnostic_path: str | None = None,
    use_lexical_fallback: bool = False,
    source_filenames: List[str] | None = None,
) -> List[Tuple[Dict[str, Any], float]]:
    """Retrieve, optionally threshold, and rerank document chunks."""
    store = FAISSVectorStore(session_id)
    fetch_k = max(settings.RERANKER_FETCH_K, top_k or settings.TOP_K_RESULTS)
    comparative_query = _is_comparative_query(query)
    retrieval_started = perf_counter()
    search_kwargs: Dict[str, Any] = {
        "top_k": fetch_k,
        "source_filenames": source_filenames,
    }
    if comparative_query:
        search_kwargs["diversify_sources"] = True
    results = store.search(query, **search_kwargs)
    candidate_count = len(results)
    thresholded_results = (
        [item for item in results if item[1] >= minimum_score]
        if minimum_score is not None
        else results
    )
    if settings.DEBUG:
        logger.debug(
            "retrieval_after_faiss",
            extra={
                "event": "retrieval_after_faiss",
                "session_id": store.session_id,
                "query": query,
                "faiss_fetch_k": fetch_k,
                "faiss_returned": candidate_count,
                "minimum_score": minimum_score,
                "threshold_cleared": len(thresholded_results),
                "threshold_policy": (
                    "diagnostic_only_comparative_query"
                    if comparative_query
                    else "pre_rerank_filter"
                ),
                "source_diversification": comparative_query,
                "score_kind": "cosine_similarity",
                "chunks": _retrieval_debug_chunks(results),
            },
        )

    if diagnostic_path == "follow_up_chat":
        index_size = store.index.ntotal if store.index is not None else 0
        top_scores = [round(score, 4) for _chunk, score in results[:3]]
        logger.info(
            "FOLLOW_UP_RETRIEVAL session_id=%s index_size=%s chunks_returned=%s "
            "top_3_similarity_scores=%s",
            store.session_id,
            index_size,
            candidate_count,
            top_scores,
        )

    # Comparative questions need evidence from multiple sources. Do not discard
    # their candidates on the embedding threshold before the reranker can compare them.
    results = results if comparative_query else thresholded_results

    if use_lexical_fallback:
        selected_sources = set(source_filenames or [])
        lexical_chunks = (
            [
                chunk
                for chunk in store.metadata
                if chunk.get("source") in selected_sources
            ]
            if selected_sources
            else store.metadata
        )
        lexical = _lexical_results(query, lexical_chunks, fetch_k)
        merged = {_chunk_key(chunk): (chunk, score) for chunk, score in results}
        for chunk, score in lexical:
            key = _chunk_key(chunk)
            existing = merged.get(key)
            if existing is None or score > existing[1]:
                merged[key] = (chunk, score)
        results = sorted(merged.values(), key=lambda item: item[1], reverse=True)

    rerank_input_count = len(results)
    if results:
        results = rerank(query, results, top_k=top_k or settings.TOP_K_RESULTS)

    if settings.DEBUG:
        logger.debug(
            "retrieval_after_rerank",
            extra={
                "event": "retrieval_after_rerank",
                "session_id": store.session_id,
                "query": query,
                "rerank_input_count": rerank_input_count,
                "rerank_returned": len(results),
                "final_top_k": top_k or settings.TOP_K_RESULTS,
                "score_kind": (
                    "reranker_logit_if_available_otherwise_retrieval_score"
                ),
                "chunks": _retrieval_debug_chunks(results),
            },
        )

    record_retrieval_trace(
        session_id=session_id,
        query=query,
        duration_ms=(perf_counter() - retrieval_started) * 1000,
        candidate_count=candidate_count,
        selected=results,
    )
    return results


def answer_from_results(
    query: str,
    results: List[Tuple[Dict[str, Any], float]],
    system_prompt: str = "",
    max_output_tokens: int | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Generate a grounded answer from already retrieved document chunks."""
    context = build_context(results)
    prompt = f"""You are a senior market research analyst. Use ONLY the provided context to answer.
If information is not in the context, say "Not covered in the uploaded documents."
Do not substitute a related metric, company, product, date, or category for the exact item asked.
Never infer a missing number from nearby figures.

CONTEXT:
{context}

CURRENT QUESTION:
{query}

Answer only the CURRENT QUESTION; do not answer or repeat any earlier question.
Start with the direct answer. For a simple fact question, use 1-3 concise sentences.
For an entity profile, use at most 6 concise bullets. For a broad report summary, use at most
8 concise bullets and 500 words. Include specific data points when available.
If the exact answer is missing, output the required not-covered sentence plus at most one brief
clarifying sentence. Do not mention these response-format instructions in the answer."""

    answer = generate(
        prompt,
        system_prompt,
        max_output_tokens=max_output_tokens,
    )
    sources = [
        {
            "filename": chunk["source"],
            "chunk_index": chunk.get("chunk_index", 0),
            "excerpt": chunk["text"][:200] + "…",
            "relevance_score": round(score, 4),
        }
        for chunk, score in results
    ]
    return answer, sources


def rag_query(
    session_id: str,
    query: str,
    system_prompt: str = "",
    top_k: int = None,
    source_filenames: List[str] | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Run a strictly document-grounded RAG query."""
    results = retrieve_results(
        session_id,
        query,
        top_k=top_k,
        source_filenames=source_filenames,
    )
    if not results:
        logger.warning("[%s] No chunks found for query: %s", session_id, query[:80])
        return NO_DOCUMENT_CONTEXT, []
    return answer_from_results(query, results, system_prompt)
