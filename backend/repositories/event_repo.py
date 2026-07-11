# repositories/event_repo.py
"""
Seen-job tracking and an event timeline, scoped per user.

`seen_jobs` records every job id a user has encountered (including ones
rejected before scoring) so we never re-fetch or re-classify the same
posting for the same user.

`events` is an append-only log of what happened and when, per user.
"""

import json
from datetime import datetime, timezone

from core import database as db
from core.logger import get_logger

logger = get_logger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# === Seen jobs ===


def seen_ids(user_id: str) -> set:
    """Return all job ids this user has already encountered."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id FROM seen_jobs WHERE user_id = ?", (user_id,)
        ).fetchall()
    return {r["id"] for r in rows if r["id"]}


def mark_seen(job, user_id: str, decision: str) -> None:
    """Record a job as seen for this user with the decision made about it."""
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO seen_jobs (id, user_id, source, title, first_seen, decision)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET decision = excluded.decision
            """,
            (job.id, user_id, job.source, job.title, _now(), decision),
        )


def block(job_id: str, user_id: str) -> None:
    """Mark a job id as 'deleted' for this user so the funnel never resurfaces it."""
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO seen_jobs (id, user_id, source, title, first_seen, decision)
            VALUES (?, ?, '', '', ?, 'deleted')
            ON CONFLICT(id) DO UPDATE SET decision = 'deleted'
            """,
            (job_id, user_id, _now()),
        )


def unblock(job_id: str, user_id: str) -> None:
    """Reverse a delete decision after a restore (timeline stays truthful)."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE seen_jobs SET decision = 'restored' "
            "WHERE id = ? AND user_id = ? AND decision = 'deleted'",
            (job_id, user_id),
        )


# === Events ===


def log_event(
    user_id: str, event_type: str, job_id: str = "", detail: str = ""
) -> None:
    """Append an event to this user's timeline."""
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO events (user_id, type, job_id, detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, event_type, job_id, detail, _now()),
        )


def recent_events(user_id: str, limit: int = 50) -> list[dict]:
    """Return the most recent events for this user, newest first."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT type, job_id, detail, created_at FROM events "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def last_run(user_id: str) -> dict | None:
    """Return {at, fetched, scored, stopped} for this user's most recent run.

    None when the user has never run a fetch. Corrupt detail JSON degrades
    to zero counts rather than failing the state endpoint.
    """
    with db.connect() as conn:
        row = conn.execute(
            "SELECT detail, created_at FROM events "
            "WHERE user_id = ? AND type = 'run' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    try:
        detail = json.loads(row["detail"] or "{}")
    except (ValueError, TypeError):
        logger.warning("Corrupt run detail for user %s - using empty", user_id)
        detail = {}
    return {
        "at": row["created_at"],
        "fetched": int(detail.get("fetched") or 0),
        "scored": int(detail.get("scored") or 0),
        "stopped": bool(detail.get("stopped")),
    }


# === Stats (for the live dashboard) ===


def stats(user_id: str) -> dict:
    """Aggregate counts for this user's metrics header."""
    with db.connect() as conn:
        scored = conn.execute(
            "SELECT COUNT(*) AS n FROM matches WHERE user_id = ? AND deleted = 0",
            (user_id,),
        ).fetchone()["n"]
        applied = conn.execute(
            "SELECT COUNT(*) AS n FROM matches "
            "WHERE user_id = ? AND applied = 1 AND deleted = 0",
            (user_id,),
        ).fetchone()["n"]
        seen = conn.execute(
            "SELECT COUNT(*) AS n FROM seen_jobs WHERE user_id = ?", (user_id,)
        ).fetchone()["n"]
        good = conn.execute(
            "SELECT COUNT(*) AS n FROM matches "
            "WHERE user_id = ? AND score >= 60 AND deleted = 0",
            (user_id,),
        ).fetchone()["n"]
    return {"seen": seen, "scored": scored, "applied": applied, "good": good}


def clear(user_id: str) -> None:
    """Wipe seen-jobs and events for this user (used alongside match_repo.clear)."""
    with db.connect() as conn:
        conn.execute("DELETE FROM seen_jobs WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
