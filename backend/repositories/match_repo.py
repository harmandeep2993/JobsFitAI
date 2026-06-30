# repositories/match_repo.py
"""
Persistence for scored job matches (SQLite-backed), scoped per user.

Every function takes user_id as its first parameter so each user only
sees and modifies their own matches.
"""

import json

from core import database as db
from core.logger import get_logger

logger = get_logger(__name__)

# Columns written on every upsert.
_COLUMNS = (
    "id",
    "source",
    "title",
    "company",
    "location",
    "url",
    "language",
    "posted_at",
    "score",
    "label",
    "matched_required",
    "missing_required",
    "scored_at",
)

# Columns returned to the UI (jd_json is large - excluded from list view).
_LIST_COLS = (
    "id, source, title, company, location, url, language, posted_at, "
    "score, label, matched_required, missing_required, scored_at, applied, status, app_status"
)

_VALID_APP_STATUSES = {"", "applied", "interview", "offer", "rejected"}


def known_ids(user_id: str) -> set:
    """Return the set of job ids already scored and stored for this user."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id FROM matches WHERE user_id = ?", (user_id,)
        ).fetchall()
    return {r["id"] for r in rows if r["id"]}


def upsert(user_id: str, items: list[dict]) -> None:
    """Insert or update scored items by id for this user (stores extracted JD too)."""
    if not items:
        return

    sql = """
        INSERT INTO matches
            (id, user_id, source, title, company, location, url, language, posted_at,
             score, label, matched_required, missing_required, scored_at,
             jd_json, section_scores, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            source=excluded.source, title=excluded.title, company=excluded.company,
            location=excluded.location, url=excluded.url, language=excluded.language,
            posted_at=excluded.posted_at, score=excluded.score, label=excluded.label,
            matched_required=excluded.matched_required,
            missing_required=excluded.missing_required, scored_at=excluded.scored_at,
            jd_json=excluded.jd_json, section_scores=excluded.section_scores,
            status=excluded.status
    """
    rows = [
        (
            it.get("id"),
            user_id,
            it.get("source"),
            it.get("title"),
            it.get("company"),
            it.get("location"),
            it.get("url"),
            it.get("language"),
            it.get("posted_at"),
            it.get("score"),
            it.get("label"),
            json.dumps(it.get("matched_required", [])),
            json.dumps(it.get("missing_required", [])),
            it.get("scored_at"),
            json.dumps(it.get("jd_json")) if it.get("jd_json") is not None else None,
            json.dumps(it.get("section_scores", {})),
            it.get("status", "scored"),
        )
        for it in items
    ]
    with db.connect() as conn:
        conn.executemany(sql, rows)


def upsert_pending(user_id: str, job) -> None:
    """Store a job's metadata immediately (status='pending') before scoring."""
    upsert(
        user_id,
        [
            {
                "id": job.id,
                "source": job.source,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "language": job.language,
                "posted_at": job.posted_at,
                "score": 0,
                "label": "",
                "matched_required": [],
                "missing_required": [],
                "section_scores": {},
                "scored_at": "",
                "jd_json": None,
                "status": "pending",
            }
        ],
    )


def set_status(user_id: str, job_id: str, status: str) -> None:
    """Update only a job's status (e.g. 'jd_unavailable') for this user."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET status = ? WHERE id = ? AND user_id = ?",
            (status, job_id, user_id),
        )


def get_all(user_id: str) -> list[dict]:
    """Return all stored matches for this user (no jd_json), highest score first."""
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT {_LIST_COLS} FROM matches WHERE user_id = ? ORDER BY score DESC",
            (user_id,),
        ).fetchall()

    out = []
    for row in rows:
        job = dict(row)
        try:
            job["matched_required"] = json.loads(job.get("matched_required") or "[]")
        except (ValueError, TypeError):
            logger.warning(
                "Corrupt matched_required for job %s - using []", job.get("id")
            )
            job["matched_required"] = []
        try:
            job["missing_required"] = json.loads(job.get("missing_required") or "[]")
        except (ValueError, TypeError):
            logger.warning(
                "Corrupt missing_required for job %s - using []", job.get("id")
            )
            job["missing_required"] = []
        out.append(job)
    return out


def rows_with_jd(user_id: str) -> list[dict]:
    """Return [{id, jd}] for every stored job for this user that has a cached JD."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, jd_json FROM matches WHERE user_id = ? AND jd_json IS NOT NULL",
            (user_id,),
        ).fetchall()
    out = []
    for r in rows:
        try:
            out.append({"id": r["id"], "jd": json.loads(r["jd_json"])})
        except (ValueError, TypeError):
            continue
    return out


def update_score(user_id: str, job_id: str, result: dict) -> None:
    """Update scoring fields for a job (used when re-scoring against a new resume).

    Also clears the cached summary, which is now stale for the new resume.
    """
    with db.connect() as conn:
        conn.execute(
            """
            UPDATE matches SET score=?, label=?, matched_required=?,
                missing_required=?, section_scores=?, summary=NULL
            WHERE id=? AND user_id=?
            """,
            (
                result.get("overall_score", 0),
                result.get("label", ""),
                json.dumps(result.get("matched_required", [])),
                json.dumps(result.get("missing_required", [])),
                json.dumps(result.get("section_scores", {})),
                job_id,
                user_id,
            ),
        )


def get_one(user_id: str, job_id: str) -> dict | None:
    """Return a single match row with jd/section_scores parsed, or None."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM matches WHERE id=? AND user_id=?", (job_id, user_id)
        ).fetchone()
    if not row:
        return None
    job = dict(row)
    for field, default, raw in (
        ("matched_required", [], job.get("matched_required") or "[]"),
        ("missing_required", [], job.get("missing_required") or "[]"),
        ("section_scores", {}, job.get("section_scores") or "{}"),
    ):
        try:
            job[field] = json.loads(raw)
        except (ValueError, TypeError):
            logger.warning(
                "Corrupt %s for job %s - using default", field, job.get("id")
            )
            job[field] = default
    try:
        job["jd_json"] = json.loads(job["jd_json"]) if job.get("jd_json") else {}
    except (ValueError, TypeError):
        logger.warning("Corrupt jd_json for job %s - using {}", job.get("id"))
        job["jd_json"] = {}
    return job


def set_summary(user_id: str, job_id: str, summary: str) -> None:
    """Cache a generated summary for a job belonging to this user."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET summary=? WHERE id=? AND user_id=?",
            (summary, job_id, user_id),
        )


def set_applied(user_id: str, job_id: str, applied: bool) -> None:
    """Mark a stored job as applied / not applied for this user."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET applied = ? WHERE id = ? AND user_id = ?",
            (1 if applied else 0, job_id, user_id),
        )


def set_app_status(user_id: str, job_id: str, status: str) -> None:
    """Set the application status for a job (applied/interview/offer/rejected)."""
    status = (status or "").strip().lower()
    if status not in _VALID_APP_STATUSES:
        return
    applied = 1 if status else 0
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET app_status = ?, applied = ? WHERE id = ? AND user_id = ?",
            (status, applied, job_id, user_id),
        )


def set_status_by_id(user_id: str, job_id: str, status: str) -> None:
    """Update only a job's status field for this user (alias kept for callers using old name)."""
    set_status(user_id, job_id, status)


def delete(user_id: str, job_id: str) -> None:
    """Remove a single match belonging to this user."""
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM matches WHERE id = ? AND user_id = ?", (job_id, user_id)
        )


def clear(user_id: str) -> None:
    """Remove all stored matches for this user."""
    with db.connect() as conn:
        conn.execute("DELETE FROM matches WHERE user_id = ?", (user_id,))
