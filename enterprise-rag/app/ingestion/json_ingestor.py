"""JSON log ingestion helpers."""

from __future__ import annotations

import json
from pathlib import Path


def validate_json(path: str | Path) -> int:
    json_path = Path(path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict) and isinstance(payload.get("events"), list):
        return len(payload["events"])
    return 1
