# src/services/cache_store.py
"""
SQLite-backed cache for /api/analyze results.

Keyed on a SHA-256 hex digest of "{resume_id or tmp}::{jd_text}".
Stores the full JSON payload (score, label, html) so repeated identical
requests skip all LLM calls.
"""

import json
from datetime import datetime, timezone

from src.services import db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get(cache_hash: str) -> dict | None:
    """Return cached result dict or None on miss."""
    try:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT result_json FROM analysis_cache WHERE hash=?",
                (cache_hash,),
            ).fetchone()
        if row:
            return json.loads(row["result_json"])
    except Exception as e:
        logger.warning("cache_store.get failed: %s", e)
    return None


def set(cache_hash: str, payload: dict) -> None:
    """Store result payload. Non-fatal on any error."""
    try:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with db.connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO analysis_cache (hash, result_json, created_at)
                   VALUES (?, ?, ?)""",
                (cache_hash, json.dumps(payload), now),
            )
    except Exception as e:
        logger.warning("cache_store.set failed: %s", e)
