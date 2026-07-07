# api/routes/resume_improve.py
"""
/api/improve-resume endpoint - resume rewrite.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.routes.auth import get_current_user
from core.logger import get_logger
from services.extractors.jd_extractor import extract_jd
from services.resume_rewriter import improve_resume
from schemas.improve import ImproveResumeRequest

logger = get_logger(__name__)

router = APIRouter()


@router.post("/improve-resume")
async def api_improve_resume(
    body: ImproveResumeRequest,
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """
    Generate JD-aligned bullets from all stored resumes.

    Accepts {jd, gaps, strengths}. Pulls extracted JSON from every stored
    resume slot, merges the data, and returns before/after bullet pairs
    grouped by source (Experience, Education, Certifications, Projects).
    """
    jd_text = (body.jd or "").strip()
    gaps = body.gaps or []
    strengths = body.strengths or []

    if len(jd_text) < 30:
        raise HTTPException(status_code=400, detail="jd_required")

    jd_json = await run_in_threadpool(extract_jd, jd_text)
    result = await run_in_threadpool(
        improve_resume, current_user["id"], jd_json, gaps, strengths
    )
    return JSONResponse(result)
