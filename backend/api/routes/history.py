# api/routes/history.py
"""
/api/history endpoint - per-user history of analyses, fetcher runs, applications.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.routes.auth import get_current_user
from core import database as db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Cap per history section - the UI shows a timeline, not a full export.
_HISTORY_LIMIT = 100


@router.get("/history")
async def api_history(
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Return the current user's history: analyser runs, fetcher runs, applications."""
    user_id = current_user["id"]
    with db.connect() as conn:
        analyses = conn.execute(
            """SELECT a.jd_snippet, a.score, a.label, a.scored_at,
                      r.label AS resume_label, r.slot
               FROM analyses a
               LEFT JOIN resumes r ON r.id = a.resume_id
               WHERE a.user_id = ?
               ORDER BY a.scored_at DESC LIMIT ?""",
            (user_id, _HISTORY_LIMIT),
        ).fetchall()

        fetcher_runs = conn.execute(
            """SELECT detail, created_at FROM events
               WHERE type = 'run' AND user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, _HISTORY_LIMIT),
        ).fetchall()

        applications = conn.execute(
            """SELECT e.created_at AS applied_at, m.title, m.company, m.url,
                      m.score, m.label, m.app_status
               FROM events e
               LEFT JOIN matches m ON m.id = e.job_id
               WHERE e.type = 'applied' AND e.user_id = ?
               ORDER BY e.id DESC LIMIT ?""",
            (user_id, _HISTORY_LIMIT),
        ).fetchall()

    return JSONResponse(
        {
            "ok": True,
            "analyses": [dict(r) for r in analyses],
            "fetcher_runs": [dict(r) for r in fetcher_runs],
            "applications": [dict(r) for r in applications],
        }
    )
