# repositories/match_repo.py
"""
Persistence for scored job matches (SQLite-backed).

Keeps the same API the rest of the app uses (known_ids / upsert / get_all /
clear); storage moved from a JSON file to SQLite (core/db.py) so it
queries cleanly and dedupes by primary key.
"""

import json

from core import database as db
from core.logger import get_logger

logger = get_logger(__name__)

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


def known_ids() -> set:
    """Return the set of job ids already scored and stored."""
    with db.connect() as conn:
        rows = conn.execute("SELECT id FROM matches").fetchall()
    return {r["id"] for r in rows if r["id"]}


def upsert(items: list[dict]) -> None:
    """Insert or update scored items by id (stores the extracted JD too)."""
    if not items:
        return

    sql = """
        INSERT INTO matches
            (id, source, title, company, location, url, language, posted_at,
             score, label, matched_required, missing_required, scored_at,
             jd_json, section_scores, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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


def upsert_pending(job) -> None:
    """Store a job's metadata immediately (status='pending'), before scoring."""
    upsert(
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
        ]
    )


def set_status(job_id: str, status: str) -> None:
    """Update only a job's status (e.g. 'jd_unavailable')."""
    with db.connect() as conn:
        conn.execute("UPDATE matches SET status = ? WHERE id = ?", (status, job_id))


# Columns returned to the UI (jd_json is large - excluded).
_LIST_COLS = (
    "id, source, title, company, location, url, language, posted_at, "
    "score, label, matched_required, missing_required, scored_at, applied, status, app_status"
)


def get_all() -> list[dict]:
    """Return all stored matches (without the bulky jd_json), highest score first."""
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT {_LIST_COLS} FROM matches ORDER BY score DESC"
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


def rows_with_jd() -> list[dict]:
    """Return [{id, jd}] for every stored job that has a cached JD."""
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, jd_json FROM matches WHERE jd_json IS NOT NULL"
        ).fetchall()
    out = []
    for r in rows:
        try:
            out.append({"id": r["id"], "jd": json.loads(r["jd_json"])})
        except (ValueError, TypeError):
            continue
    return out


def update_score(job_id: str, result: dict) -> None:
    """Update scoring fields for a job (used when re-scoring a new resume).

    Also clears the cached summary, which is now stale for the new resume.
    """
    with db.connect() as conn:
        conn.execute(
            """
            UPDATE matches SET score=?, label=?, matched_required=?,
                missing_required=?, section_scores=?, summary=NULL
            WHERE id=?
            """,
            (
                result.get("overall_score", 0),
                result.get("label", ""),
                json.dumps(result.get("matched_required", [])),
                json.dumps(result.get("missing_required", [])),
                json.dumps(result.get("section_scores", {})),
                job_id,
            ),
        )


def get_one(job_id: str) -> dict | None:
    """Return a single match row with jd/section_scores parsed, or None."""
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM matches WHERE id=?", (job_id,)).fetchone()
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


def set_summary(job_id: str, summary: str) -> None:
    """Cache a generated summary for a job."""
    with db.connect() as conn:
        conn.execute("UPDATE matches SET summary=? WHERE id=?", (summary, job_id))


def set_applied(job_id: str, applied: bool) -> None:
    """Mark a stored job as applied / not applied."""
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET applied = ? WHERE id = ?",
            (1 if applied else 0, job_id),
        )


_VALID_APP_STATUSES = {"", "applied", "interview", "offer", "rejected"}


def set_app_status(job_id: str, status: str) -> None:
    """Set the application status for a job (applied/interview/offer/rejected)."""
    status = (status or "").strip().lower()
    if status not in _VALID_APP_STATUSES:
        return
    applied = 1 if status else 0
    with db.connect() as conn:
        conn.execute(
            "UPDATE matches SET app_status = ?, applied = ? WHERE id = ?",
            (status, applied, job_id),
        )


def delete(job_id: str) -> None:
    """Remove a single match."""
    with db.connect() as conn:
        conn.execute("DELETE FROM matches WHERE id = ?", (job_id,))


def clear() -> None:
    """Remove all stored matches."""
    with db.connect() as conn:
        conn.execute("DELETE FROM matches")
