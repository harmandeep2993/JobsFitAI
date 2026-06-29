# api/routes/improve.py
"""
/api/improve-resume endpoint - resume rewrite.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core.logger import get_logger
from extractors.jd import extract_jd
from services.rewrite import improve_resume

logger = get_logger(__name__)

router = APIRouter()


@router.post("/improve-resume")
async def api_improve_resume(request: Request) -> JSONResponse:
    """
    Generate JD-aligned bullets from all stored resumes.

    Accepts {jd, gaps, strengths}. Pulls extracted JSON from every stored
    resume slot, merges the data, and returns before/after bullet pairs
    grouped by source (Experience, Education, Certifications, Projects).
    """
    body = await request.json()
    jd_text = (body.get("jd") or "").strip()
    gaps = body.get("gaps") or []
    strengths = body.get("strengths") or []

    if len(jd_text) < 30:
        return JSONResponse({"ok": False, "error": "jd_required"}, status_code=400)

    jd_json = await run_in_threadpool(extract_jd, jd_text)
    result = await run_in_threadpool(improve_resume, "local", jd_json, gaps, strengths)
    return JSONResponse(result)
