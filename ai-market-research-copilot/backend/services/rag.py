from time import perf_counter
from typing import Any, Dict, List, Tuple

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.observability import record_retrieval_trace

from .llm import generate, rerank
from .vector_store import FAISSVectorStore

logger = get_logger(__name__)
settings = get_settings()


def build_context(
    results: List[Tuple[Dict[str, Any], float]], max_chars: int = 6000
) -> str:
    """Concatenate retrieved chunks into a context string with citations."""
    parts = []
    total = 0
    for chunk, _score in results:
        snippet = f"[Source: {chunk['source']}, Page {chunk.get('page', '?')}]\n{chunk['text']}"
        if total + len(snippet) > max_chars:
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n\n---\n\n".join(parts)


def rag_query(
    session_id: str,
    query: str,
    system_prompt: str = "",
    top_k: int = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run a RAG query:
      1. Retrieve top-k chunks from FAISS
      2. Build context
      3. Call LLM with context + query
    Returns (answer, list_of_source_dicts)
    """
    store = FAISSVectorStore(session_id)
    # Fetch more candidates than needed so the reranker has room to work
    fetch_k = max(settings.RERANKER_FETCH_K, top_k or settings.TOP_K_RESULTS)
    retrieval_started = perf_counter()
    results = store.search(query, top_k=fetch_k)

    if not results:
        record_retrieval_trace(
            session_id=session_id,
            query=query,
            duration_ms=(perf_counter() - retrieval_started) * 1000,
            candidate_count=0,
            selected=[],
        )
        logger.warning(f"[{session_id}] No chunks found for query: {query[:80]}")
        answer = (
            "No indexed document context was found for this question. "
            "Upload relevant source documents or ask about content already indexed in this session."
        )
        return answer, []

    # P2: Rerank candidates → keep only top_k most relevant
    candidate_count = len(results)
    results = rerank(query, results, top_k=top_k or settings.TOP_K_RESULTS)
    record_retrieval_trace(
        session_id=session_id,
        query=query,
        duration_ms=(perf_counter() - retrieval_started) * 1000,
        candidate_count=candidate_count,
        selected=results,
    )

    context = build_context(results)

    prompt = f"""You are a senior market research analyst. Use ONLY the provided context to answer.
If information is not in the context, say "Not covered in the uploaded documents."

CONTEXT:
{context}

QUESTION:
{query}

Provide a detailed, structured answer with specific data points where available."""

    answer = generate(prompt, system_prompt)

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
