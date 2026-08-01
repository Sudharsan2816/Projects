from time import perf_counter
from typing import Any, Dict, Generator, List, Tuple

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.observability import record_retrieval_trace

from .llm import generate_stream, rerank
from .rag import rag_query
from .vector_store import FAISSVectorStore

logger = get_logger(__name__)
settings = get_settings()

SYSTEM = """You are an AI assistant specializing in market research analysis.
Answer questions using uploaded document context only.
Be concise, precise, and cite sources when available. If context is missing, say so."""


def chat(
    session_id: str,
    user_message: str,
    history: List[Dict[str, str]] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run a chat turn with optional history context.
    Returns (answer_text, sources_list).
    """
    # Build history context string
    history_text = ""
    if history:
        recent = history[-settings.CHAT_HISTORY_CONTEXT_LIMIT :]  # keep recent context window
        for msg in recent:
            role = msg.get("role", "user").capitalize()
            history_text += f"{role}: {msg.get('content', '')}\n"

    if history_text:
        full_query = f"""Previous conversation:
{history_text}

Current question: {user_message}"""
    else:
        full_query = user_message

    answer, sources = rag_query(
        session_id=session_id,
        query=full_query,
        system_prompt=SYSTEM,
    )
    return answer, sources


def chat_stream(
    session_id: str,
    user_message: str,
    history: List[Dict[str, str]] = None,
) -> Generator[Tuple[str, Any], None, None]:
    """
    Streaming version of chat().
    Yields (token, None) for each text chunk, then (None, sources) at the end.
    """
    history_text = ""
    if history:
        for msg in history[-settings.CHAT_HISTORY_CONTEXT_LIMIT :]:
            history_text += f"{msg.get('role','user').capitalize()}: {msg.get('content','')}\n"

    full_query = (
        f"Previous conversation:\n{history_text}\nCurrent question: {user_message}"
        if history_text
        else user_message
    )

    # Retrieve + rerank sources before streaming
    store = FAISSVectorStore(session_id)
    retrieval_started = perf_counter()
    results = store.search(full_query, top_k=settings.RERANKER_FETCH_K)
    sources = []

    if results:
        candidate_count = len(results)
        results = rerank(full_query, results, top_k=settings.TOP_K_RESULTS)
        record_retrieval_trace(
            session_id=session_id,
            query=full_query,
            duration_ms=(perf_counter() - retrieval_started) * 1000,
            candidate_count=candidate_count,
            selected=results,
        )
        from .rag import build_context
        context = build_context(results)
        prompt = f"""You are a senior market research analyst. Use ONLY the provided context to answer.
If information is not in the context, say "Not covered in the uploaded documents."

CONTEXT:
{context}

QUESTION:
{full_query}

Provide a detailed, structured answer with specific data points where available."""
        sources = [
            {
                "filename": chunk["source"],
                "chunk_index": chunk.get("chunk_index", 0),
                "excerpt": chunk["text"][:200] + "…",
                "relevance_score": round(score, 4),
            }
            for chunk, score in results
        ]
    else:
        record_retrieval_trace(
            session_id=session_id,
            query=full_query,
            duration_ms=(perf_counter() - retrieval_started) * 1000,
            candidate_count=0,
            selected=[],
        )
        yield (
            "No indexed document context was found for this question. "
            "Upload relevant source documents or ask about content already indexed in this session.",
            None,
        )
        yield None, sources
        return

    for token in generate_stream(prompt, SYSTEM):
        yield token, None

    yield None, sources
