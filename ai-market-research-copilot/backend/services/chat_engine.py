import json
from typing import List, Dict, Any, Tuple

from .rag import rag_query
from .llm import generate
from backend.core.logging import get_logger

logger = get_logger(__name__)

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
        recent = history[-6:]  # keep last 3 exchanges
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
