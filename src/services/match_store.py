# src/services/match_store.py
"""
Persistence for scored job matches.

Stores results in a local JSON file (data/ is gitignored) so the Job
Matches dashboard keeps history across restarts and can deduplicate jobs
it has already scored. Keyed by job id.
"""

import json
import threading
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

STORE_PATH = Path("data/job_matches.json")
_lock = threading.Lock()


def _load() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to read match store: %s", e)
        return []


def _save(items: list[dict]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def known_ids() -> set:
    """Return the set of job ids already scored and stored."""
    with _lock:
        return {it.get("id") for it in _load() if it.get("id")}


def upsert(items: list[dict]) -> None:
    """Insert or update scored items by id."""
    if not items:
        return
    with _lock:
        by_id = {it.get("id"): it for it in _load()}
        for it in items:
            by_id[it.get("id")] = it
        _save(list(by_id.values()))


def get_all() -> list[dict]:
    """Return all stored matches, highest score first."""
    with _lock:
        items = _load()
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return items


def clear() -> None:
    """Remove all stored matches."""
    with _lock:
        _save([])
