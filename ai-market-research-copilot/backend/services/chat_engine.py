import json
from typing import List, Dict, Any, Tuple, Generator

from .rag import rag_query
from .llm import generate, generate_stream, rerank
from .vector_store import FAISSVectorStore
from .embedder import embed_query
from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

SYSTEM = """You are an AI assistant specializing in market research analysis.
Answer questions based on uploaded documents and your knowledge of market research.
Be concise, precise, and cite sources when available."""


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
    results = store.search(full_query, top_k=settings.RERANKER_FETCH_K)
    sources = []

    if results:
        results = rerank(full_query, results, top_k=settings.TOP_K_RESULTS)
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
        prompt = f"Answer the following market research question:\n{full_query}"

    for token in generate_stream(prompt, SYSTEM):
        yield token, None

    yield None, sources
