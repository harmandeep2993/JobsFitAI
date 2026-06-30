# api/routes/ats_maker.py
"""
/api/ats/* endpoints - ATS optimizer.
"""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from core.logger import get_logger
from services.extractors.jd_extractor import extract_jd
from services.parsers import extract_all_text
from repositories import resume_repo as resume_store
from services.ats import ats_check
from schemas.ats import AtsCheckRequest, AtsOptimiseRequest

logger = get_logger(__name__)

router = APIRouter()

_USER = "local"


@router.post("/check")
async def api_ats_check(body: AtsCheckRequest) -> JSONResponse:
    """
    Lightweight ATS scan - no LLM, no keyword injection.

    Accepts {resume_id, jd?}. Returns section heading flags, formatting flags,
    keyword coverage (if JD provided), and a composite ATS score.
    """
    resume_id = (body.resume_id or "").strip()
    jd_text = (body.jd or "").strip()

    if not resume_id:
        raise HTTPException(status_code=400, detail="resume_id_required")

    record = resume_store.get(_USER, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="resume_not_found")

    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        raise HTTPException(status_code=422, detail="could_not_read_resume")

    required_skills = None
    if jd_text and len(jd_text) >= 50:
        jd_json = await run_in_threadpool(extract_jd, jd_text)
        required_skills = jd_json.get("required_skills") or []

    result = await run_in_threadpool(ats_check, resume_text, required_skills)
    return JSONResponse({"ok": True, **result})


@router.post("/optimise")
async def api_ats_optimise(body: AtsOptimiseRequest) -> JSONResponse:
    """
    Full ATS optimization pipeline with LLM.

    Accepts {resume_id, jd}. Returns a complete ATS-optimised resume.
    """
    resume_id = (body.resume_id or "").strip()
    jd_text = (body.jd or "").strip()

    if not resume_id:
        raise HTTPException(status_code=400, detail="resume_id_required")
    if len(jd_text) < 50:
        raise HTTPException(status_code=400, detail="jd_required")

    record = resume_store.get(_USER, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="resume_not_found")

    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        raise HTTPException(status_code=422, detail="could_not_read_resume")

    # TODO: implement LLM-powered ATS resume generation in services/ats.py
    # Should call generate_ats_resume(resume_text, jd_text) and return
    # {resume, coverage_before, coverage_after, section_flags, formatting_flags, plain_text}
    raise HTTPException(status_code=501, detail="ats_optimise_not_implemented")
