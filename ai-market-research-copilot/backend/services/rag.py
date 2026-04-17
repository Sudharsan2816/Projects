from typing import List, Tuple, Dict, Any

from .vector_store import FAISSVectorStore
from .llm import generate
from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def build_context(
    results: List[Tuple[Dict[str, Any], float]], max_chars: int = 6000
) -> str:
    """Concatenate retrieved chunks into a context string with citations."""
    parts = []
    total = 0
    for chunk, score in results:
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
    results = store.search(query, top_k=top_k or settings.TOP_K_RESULTS)

    if not results:
        logger.warning(f"[{session_id}] No chunks found for query: {query[:80]}")
        # Fallback: answer from LLM knowledge alone
        answer = generate(
            f"Answer the following question about market research as best as possible:\n{query}",
            system_prompt,
        )
        return answer, []

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
