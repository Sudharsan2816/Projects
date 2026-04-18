import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.db_models import ChatMessage
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.chat_engine import chat
from backend.core.logging import get_logger

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = get_logger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # Load history
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    try:
        answer, sources = chat(
            session_id=request.session_id,
            user_message=request.message,
            history=history,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # Persist user message
    db.add(ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message,
    ))

    # Persist assistant message
    db.add(ChatMessage(
        session_id=request.session_id,
        role="assistant",
        content=answer,
        sources=json.dumps(sources) if sources else None,
    ))
    db.commit()

    return ChatResponse(role="assistant", content=answer, sources=sources)


@router.get("/{session_id}/history")
def get_history(session_id: str, db: Session = Depends(get_db)):
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
            "created_at": m.created_at,
        }
        for m in messages
    ]


@router.delete("/{session_id}/history")
def clear_history(session_id: str, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    return {"status": "cleared"}
