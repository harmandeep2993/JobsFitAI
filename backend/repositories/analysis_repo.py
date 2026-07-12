"""
Per-resume analysis history store.

Records every successful analyze() run, keyed on (resume_id, jd_snippet).
Repeated runs for the same resume+JD pair update the existing row rather
than inserting a duplicate, so the history shows the most recent score.
"""

import uuid
from datetime import datetime, timezone

from core import database as db

# Maximum characters stored in the jd_snippet column.
# Long enough to be a useful identifier in the history view, short enough
# to stay well within SQLite's default page size. Truncation is applied
# inside save() so callers pass the raw JD text.
_SNIPPET_MAX = 120


def save(
    user_id: str,
    resume_id: str,
    jd_snippet: str,
    score: float,
    label: str,
    cache_hash: str = "",
) -> None:
    """Upsert an analysis result; update score/label if the same resume+JD pair already exists.

    cache_hash links the row to the full cached payload in analysis_cache so
    the history view can reopen the complete result.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snippet = (jd_snippet or "")[:_SNIPPET_MAX]
    with db.connect() as conn:
        existing = conn.execute(
            "SELECT id FROM analyses WHERE user_id=? AND resume_id=? AND jd_snippet=?",
            (user_id, resume_id, snippet),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE analyses SET score=?, label=?, cache_hash=?, scored_at=? WHERE id=?",
                (round(score), label, cache_hash, now, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO analyses (id, user_id, resume_id, jd_snippet, score, label, cache_hash, scored_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    user_id,
                    resume_id,
                    snippet,
                    round(score),
                    label,
                    cache_hash,
                    now,
                ),
            )


def owns_hash(user_id: str, cache_hash: str) -> bool:
    """Return True if this user has an analysis row pointing at cache_hash."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM analyses WHERE user_id=? AND cache_hash=? LIMIT 1",
            (user_id, cache_hash),
        ).fetchone()
    return row is not None


def get_for_resume(resume_id: str, limit: int = 5) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT jd_snippet, score, label, scored_at
               FROM analyses WHERE resume_id=? ORDER BY scored_at DESC LIMIT ?""",
            (resume_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
