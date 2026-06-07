# src/services/match_store.py
"""
Persistence for scored job matches (SQLite-backed).

Keeps the same API the rest of the app uses (known_ids / upsert / get_all /
clear); storage moved from a JSON file to SQLite (src/services/db.py) so it
queries cleanly and dedupes by primary key.
"""

import json

from src.services import db
from src.utils.logger import get_logger

logger = get_logger(__name__)

_COLUMNS = (
    "id", "source", "title", "company", "location", "url", "language",
    "posted_at", "score", "label", "matched_required", "missing_required",
    "scored_at",
)


def known_ids() -> set:
    """Return the set of job ids already scored and stored."""
    with db.connect() as conn:
        rows = conn.execute("SELECT id FROM matches").fetchall()
    return {r["id"] for r in rows if r["id"]}


def upsert(items: list[dict]) -> None:
    """Insert or update scored items by id."""
    if not items:
        return

    sql = """
        INSERT INTO matches
            (id, source, title, company, location, url, language, posted_at,
             score, label, matched_required, missing_required, scored_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            source=excluded.source, title=excluded.title, company=excluded.company,
            location=excluded.location, url=excluded.url, language=excluded.language,
            posted_at=excluded.posted_at, score=excluded.score, label=excluded.label,
            matched_required=excluded.matched_required,
            missing_required=excluded.missing_required, scored_at=excluded.scored_at
    """
    rows = [
        (
            it.get("id"), it.get("source"), it.get("title"), it.get("company"),
            it.get("location"), it.get("url"), it.get("language"), it.get("posted_at"),
            it.get("score"), it.get("label"),
            json.dumps(it.get("matched_required", [])),
            json.dumps(it.get("missing_required", [])),
            it.get("scored_at"),
        )
        for it in items
    ]
    with db.connect() as conn:
        conn.executemany(sql, rows)


def get_all() -> list[dict]:
    """Return all stored matches, highest score first."""
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM matches ORDER BY score DESC").fetchall()

    out = []
    for r in rows:
        d = dict(r)
        d["matched_required"] = json.loads(d.get("matched_required") or "[]")
        d["missing_required"] = json.loads(d.get("missing_required") or "[]")
        out.append(d)
    return out


def clear() -> None:
    """Remove all stored matches."""
    with db.connect() as conn:
        conn.execute("DELETE FROM matches")
