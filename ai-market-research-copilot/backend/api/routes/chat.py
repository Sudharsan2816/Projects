import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id
from backend.models.db_models import ChatMessage
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.chat_engine import chat, chat_stream
from backend.services.llm import LLMProviderError

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)
settings = get_settings()


def _load_history(db: Session, session_id: str) -> list[dict[str, str]]:
    """Load the newest bounded history, returned in chronological order."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(settings.CHAT_HISTORY_DB_LIMIT)
        .all()
    )
    rows.reverse()
    return [{"role": message.role, "content": message.content} for message in rows]


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = normalize_session_id(request.session_id)
    user_message = request.message.strip()
    # Load history
    history = _load_history(db, session_id)

    try:
        answer, sources, answer_mode = chat(
            session_id=session_id,
            user_message=user_message,
            history=history,
        )
    except Exception as error:
        logger.error("Chat error: %s", error, exc_info=True)
        detail = str(error) if isinstance(error, LLMProviderError) else "Chat generation failed"
        raise HTTPException(status_code=502, detail=detail) from error

    # Persist user message
    db.add(ChatMessage(
        session_id=session_id,
        role="user",
        content=user_message,
    ))

    # Persist assistant message
    db.add(ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources) if sources else None,
        answer_mode=answer_mode,
    ))
    db.commit()

    return ChatResponse(
        role="assistant",
        content=answer,
        sources=sources,
        answer_mode=answer_mode,
    )


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """SSE streaming endpoint — yields text chunks then a final JSON sources line."""
    session_id = normalize_session_id(request.session_id)
    user_message = request.message.strip()
    history = _load_history(db, session_id)
    def event_stream():
        full_answer_parts = []
        sources = []
        answer_mode = None
        try:
            for chunk, src, mode in chat_stream(
                session_id=session_id,
                user_message=user_message,
                history=history,
            ):
                if chunk:
                    full_answer_parts.append(chunk)
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
                if src is not None:
                    sources.extend(src)
                if mode is not None:
                    answer_mode = mode
        except Exception as error:
            logger.error("Chat stream error: %s", error, exc_info=True)
            detail = str(error) if isinstance(error, LLMProviderError) else "Chat generation failed"
            yield f"data: {json.dumps({'error': detail})}\n\n"
            return

        full_answer = "".join(full_answer_parts)

        # Use a fresh DB session for persistence — the request-scoped one is closed by now
        from backend.core.database import SessionLocal
        persist_db = SessionLocal()
        try:
            persist_db.add(ChatMessage(session_id=session_id, role="user", content=user_message))
            persist_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_answer,
                sources=json.dumps(sources) if sources else None,
                answer_mode=answer_mode,
            ))
            persist_db.commit()
        except Exception as e:
            logger.error(f"Stream persist failed: {e}")
        finally:
            persist_db.close()

        yield f"data: {json.dumps({'done': True, 'sources': sources, 'answer_mode': answer_mode})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{session_id}/history")
def get_history(session_id: str, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": json.loads(m.sources) if m.sources else [],
            "answer_mode": m.answer_mode,
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.delete("/{session_id}/history")
def clear_history(session_id: str, db: Session = Depends(get_db)):
    session_id = normalize_session_id(session_id)
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    return {"status": "cleared"}
