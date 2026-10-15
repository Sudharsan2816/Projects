from datetime import datetime, timedelta
from uuid import uuid4

from backend.api.routes.chat import _load_history
from backend.core.database import SessionLocal, init_db
from backend.models.db_models import ChatMessage
from backend.models.db_models import Session as DBSession


def test_load_history_keeps_newest_messages_in_chronological_order():
    init_db()
    session_id = f"history-{uuid4()}"
    db = SessionLocal()
    try:
        db.add(DBSession(session_id=session_id))
        started = datetime(2026, 1, 1)
        for index in range(25):
            db.add(
                ChatMessage(
                    session_id=session_id,
                    role="user" if index % 2 == 0 else "assistant",
                    content=f"message-{index}",
                    created_at=started + timedelta(seconds=index),
                )
            )
        db.commit()

        history = _load_history(db, session_id)

        assert len(history) == 20
        assert history[0]["content"] == "message-5"
        assert history[-1]["content"] == "message-24"
    finally:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.query(DBSession).filter(DBSession.session_id == session_id).delete()
        db.commit()
        db.close()
