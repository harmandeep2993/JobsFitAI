# api/routes/history.py
"""
/api/history endpoint.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core import db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/history")
async def api_history() -> JSONResponse:
    """Return all history sources: analyser runs, fetcher runs, applications."""
    with db.connect() as conn:
        analyses = conn.execute(
            """SELECT a.jd_snippet, a.score, a.label, a.scored_at,
                      r.label AS resume_label, r.slot
               FROM analyses a
               LEFT JOIN resumes r ON r.id = a.resume_id
               ORDER BY a.scored_at DESC LIMIT 100"""
        ).fetchall()

        fetcher_runs = conn.execute(
            """SELECT detail, created_at FROM events
               WHERE type = 'run' ORDER BY id DESC LIMIT 100"""
        ).fetchall()

        applications = conn.execute(
            """SELECT e.created_at AS applied_at, m.title, m.company, m.url,
                      m.score, m.label, m.app_status
               FROM events e
               LEFT JOIN matches m ON m.id = e.job_id
               WHERE e.type = 'applied'
               ORDER BY e.id DESC LIMIT 100"""
        ).fetchall()

    return JSONResponse(
        {
            "ok": True,
            "analyses": [dict(r) for r in analyses],
            "fetcher_runs": [dict(r) for r in fetcher_runs],
            "applications": [dict(r) for r in applications],
        }
    )
