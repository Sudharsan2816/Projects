"""JSON log retriever."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import DATA_DIR


def retrieve_json_context(query: str, allowed_permissions: set[str], limit: int = 8) -> list[dict]:
    allowed = {"logs", "operational_logs", "audit_logs"} & allowed_permissions
    if not allowed:
        return []
    terms = [term for term in query.lower().split() if len(term) > 2]
    contexts: list[dict] = []
    for path in Path(DATA_DIR / "json_logs").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        events = payload if isinstance(payload, list) else payload.get("events", [payload])
        permission = "audit_logs" if "audit" in path.name.lower() else "operational_logs"
        if permission not in allowed and "logs" not in allowed:
            continue
        for event in events:
            text = json.dumps(event)
            if any(term in text.lower() for term in terms) or any(
                token in query.lower() for token in ["log", "audit", "outage", "event"]
            ):
                contexts.append(
                    {
                        "source": str(path),
                        "source_type": "json",
                        "permission": permission,
                        "content": text,
                    }
                )
            if len(contexts) >= limit:
                return contexts
    return contexts
