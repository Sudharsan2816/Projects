import re
from pathlib import Path

from fastapi import HTTPException

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def normalize_session_id(session_id: str) -> str:
    """Validate session IDs before using them in filesystem paths."""
    clean = (session_id or "").strip()
    if not _SESSION_ID_RE.fullmatch(clean):
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id. Use 1-64 letters, numbers, dots, dashes, or underscores.",
        )
    return clean


def sanitize_upload_filename(filename: str) -> str:
    """Return a path-safe upload filename while preserving the extension."""
    base_name = Path((filename or "upload").replace("\\", "/")).name.strip()
    stem = Path(base_name).stem or "upload"
    suffix = Path(base_name).suffix.lower()
    safe_stem = _SAFE_FILENAME_RE.sub("_", stem).strip("._-") or "upload"
    safe_suffix = _SAFE_FILENAME_RE.sub("", suffix)
    return f"{safe_stem[:120]}{safe_suffix[:20]}"
