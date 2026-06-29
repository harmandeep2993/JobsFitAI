# api/routes/ats.py
"""
/api/ats/* endpoints - ATS optimizer.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core.logger import get_logger
from extractors.jd import extract_jd
from parsers import extract_all_text
from repositories import resume_repo as resume_store
from services.ats import ats_check, generate_ats_resume

logger = get_logger(__name__)

router = APIRouter()

_USER = "local"


@router.post("/check")
async def api_ats_check(request: Request) -> JSONResponse:
    """
    Lightweight ATS scan - no LLM, no keyword injection.

    Accepts {resume_id, jd?}. Returns section heading flags, formatting flags,
    keyword coverage (if JD provided), and a composite ATS score.
    """
    body = await request.json()
    resume_id = (body.get("resume_id") or "").strip()
    jd_text = (body.get("jd") or "").strip()

    if not resume_id:
        return JSONResponse(
            {"ok": False, "error": "resume_id_required"}, status_code=400
        )

    record = resume_store.get(_USER, resume_id)
    if not record:
        return JSONResponse({"ok": False, "error": "resume_not_found"}, status_code=404)

    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        return JSONResponse(
            {"ok": False, "error": "could_not_read_resume"}, status_code=422
        )

    required_skills = None
    if jd_text and len(jd_text) >= 50:
        jd_json = await run_in_threadpool(extract_jd, jd_text)
        required_skills = jd_json.get("required_skills") or []

    result = await run_in_threadpool(ats_check, resume_text, required_skills)
    return JSONResponse({"ok": True, **result})


@router.post("/optimise")
async def api_ats_optimise(request: Request) -> JSONResponse:
    """
    Full ATS optimization pipeline with LLM.

    Accepts {resume_id, jd}. Returns a complete ATS-optimised resume.
    """
    body = await request.json()
    resume_id = (body.get("resume_id") or "").strip()
    jd_text = (body.get("jd") or "").strip()

    if not resume_id:
        return JSONResponse(
            {"ok": False, "error": "resume_id_required"}, status_code=400
        )
    if len(jd_text) < 50:
        return JSONResponse({"ok": False, "error": "jd_required"}, status_code=400)

    record = resume_store.get(_USER, resume_id)
    if not record:
        return JSONResponse({"ok": False, "error": "resume_not_found"}, status_code=404)

    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        return JSONResponse(
            {"ok": False, "error": "could_not_read_resume"}, status_code=422
        )

    try:
        result = await run_in_threadpool(generate_ats_resume, resume_text, jd_text)
        return JSONResponse({"ok": True, **result})
    except Exception as e:
        logger.error("ATS optimise failed: %s", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
