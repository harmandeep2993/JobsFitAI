"""
Per-resume analysis history store.

Records every successful analyze() run, keyed on (resume_id, jd_snippet).
Repeated runs for the same resume+JD pair update the existing row rather
than inserting a duplicate, so the history shows the most recent score.
"""

import uuid
from datetime import datetime, timezone

from src.services import db

# Maximum characters stored in the jd_snippet column.
# Long enough to be a useful identifier in the history view, short enough
# to stay well within SQLite's default page size. Must stay in sync with
# the truncation applied in app.py before calling save().
_SNIPPET_MAX = 120


def save(resume_id: str, jd_snippet: str, score: float, label: str) -> None:
    """Upsert an analysis result; update score/label if the same resume+JD pair already exists."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snippet = (jd_snippet or "")[:_SNIPPET_MAX]
    with db.connect() as conn:
        existing = conn.execute(
            "SELECT id FROM analyses WHERE resume_id=? AND jd_snippet=?",
            (resume_id, snippet),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE analyses SET score=?, label=?, scored_at=? WHERE id=?",
                (round(score), label, now, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO analyses (id, resume_id, jd_snippet, score, label, scored_at)
                   VALUES (?,?,?,?,?,?)""",
                (str(uuid.uuid4()), resume_id, snippet, round(score), label, now),
            )


def get_for_resume(resume_id: str, limit: int = 5) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT jd_snippet, score, label, scored_at
               FROM analyses WHERE resume_id=? ORDER BY scored_at DESC LIMIT ?""",
            (resume_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
