# repositories/event_repo.py
"""
Seen-job tracking and an event timeline.

`seen_jobs` records every job id we've encountered (including ones rejected
before scoring) so we never re-fetch or re-classify the same posting.
`events` is an append-only log of what happened and when.
"""

from datetime import datetime, timezone

from core import db
from core.logger import get_logger

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Seen jobs ---
def seen_ids() -> set:
    """All job ids we've already encountered."""
    with db.connect() as conn:
        rows = conn.execute("SELECT id FROM seen_jobs").fetchall()
    return {r["id"] for r in rows if r["id"]}


def mark_seen(job, decision: str) -> None:
    """Record a job as seen with the decision made about it."""
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO seen_jobs (id, source, title, first_seen, decision)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET decision = excluded.decision
            """,
            (job.id, job.source, job.title, _now(), decision),
        )


def block(job_id: str) -> None:
    """Mark a job id as 'deleted' so the funnel never resurfaces it."""
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO seen_jobs (id, source, title, first_seen, decision)
            VALUES (?, '', '', ?, 'deleted')
            ON CONFLICT(id) DO UPDATE SET decision = 'deleted'
            """,
            (job_id, _now()),
        )


# --- Events ---
def log_event(event_type: str, job_id: str = "", detail: str = "") -> None:
    """Append an event to the timeline."""
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO events (type, job_id, detail, created_at) VALUES (?, ?, ?, ?)",
            (event_type, job_id, detail, _now()),
        )


def recent_events(limit: int = 50) -> list[dict]:
    """Most recent events, newest first."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT type, job_id, detail, created_at FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# --- Stats (for the live dashboard) ---
def stats() -> dict:
    """Aggregate counts for the metrics header."""
    with db.connect() as conn:
        scored = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        applied = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE applied = 1"
        ).fetchone()[0]
        seen = conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
        good = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE score >= 60"
        ).fetchone()[0]
    return {"seen": seen, "scored": scored, "applied": applied, "good": good}


def clear() -> None:
    """Wipe seen-jobs and events (used alongside match_repo.clear)."""
    with db.connect() as conn:
        conn.execute("DELETE FROM seen_jobs")
        conn.execute("DELETE FROM events")
