# core/uploads.py
"""
Registry for temporary resume uploads.

Maps opaque tokens to server-side temp file paths so clients never see or
supply raw filesystem paths (which would allow arbitrary file reads).
Entries are scoped to the uploading user and expire after UPLOAD_TTL_SECONDS;
expired temp files are deleted lazily on the next register() call.
"""

import os
import threading
import time
import uuid

from core.logger import get_logger

logger = get_logger(__name__)

# Temp uploads only need to live long enough for the user to run an analysis
# after uploading; two hours covers a long form-filling session.
UPLOAD_TTL_SECONDS = 2 * 60 * 60

# token -> {"user_id", "path", "created"}
_entries: dict[str, dict] = {}
_lock = threading.Lock()


def _prune() -> None:
    """Drop expired entries and delete their temp files. Caller holds _lock."""
    now = time.monotonic()
    expired = [
        t for t, e in _entries.items() if now - e["created"] > UPLOAD_TTL_SECONDS
    ]
    for token in expired:
        entry = _entries.pop(token)
        try:
            os.remove(entry["path"])
        except OSError:
            pass


def register(user_id: str, path: str) -> str:
    """Store a temp file path for user_id and return an opaque token for it."""
    token = uuid.uuid4().hex
    with _lock:
        _prune()
        _entries[token] = {
            "user_id": user_id,
            "path": path,
            "created": time.monotonic(),
        }
    return token


def resolve(user_id: str, token: str) -> str | None:
    """Return the temp file path for token if it belongs to user_id and still exists."""
    with _lock:
        entry = _entries.get((token or "").strip())
    if not entry or entry["user_id"] != user_id:
        return None
    if not os.path.exists(entry["path"]):
        return None
    return entry["path"]
