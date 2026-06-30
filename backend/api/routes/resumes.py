# api/routes/resumes.py
"""
/api/resumes/* endpoints - stored resume management.
"""

import asyncio
import json as _json
import os
from pathlib import Path
from typing import Set

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core.config import MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from core.logger import get_logger
from core import state as session
from services.extractors.jd_extractor import extract_jd
from services.extractors.resume_extractor import extract_resume
from services.matcher.engine import match
from services.parsers import extract_all_text
from repositories import resume_repo as resume_store
from services.job_matcher import rescore_all

logger = get_logger(__name__)

router = APIRouter()

_USER = "local"

ALLOWED_EXTENSIONS: Set[str] = SUPPORTED_EXTENSIONS
MAX_FILE_MB: int = MAX_FILE_SIZE_MB

_PREVIEW_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload")
async def api_resumes_upload(request: Request) -> JSONResponse:
    """Upload a resume into a persistent slot (0=Base, 1=Tailored 1, 2=Tailored 2)."""
    form = await request.form()
    upload = form.get("file")
    slot = int(form.get("slot", 0))

    if upload is None:
        return JSONResponse({"ok": False, "error": "no file"}, status_code=400)
    if slot not in range(resume_store.MAX_SLOTS):
        return JSONResponse({"ok": False, "error": "invalid slot"}, status_code=400)

    data = await upload.read()
    filename = upload.filename or "resume"
    suffix = Path(filename).suffix.lower()

    if len(data) == 0:
        return JSONResponse({"ok": False, "error": "empty file"}, status_code=400)
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        return JSONResponse(
            {"ok": False, "error": f"file too large (max {MAX_FILE_MB} MB)"},
            status_code=400,
        )
    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {
                "ok": False,
                "error": f"unsupported file type (allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))})",
            },
            status_code=400,
        )

    mime = _PREVIEW_TYPES.get(suffix, "application/octet-stream")
    record = resume_store.save(_USER, slot, filename, data, suffix, mime)

    async def _extract_bg(rid: str, path: str) -> None:
        def _run():
            try:
                text = extract_all_text(path)
                if not text or len(text) < 50:
                    return
                extracted = extract_resume(text)
                if extracted:
                    resume_store.set_extracted(_USER, rid, _json.dumps(extracted))
                    logger.info("Background extraction done for resume %s", rid)
            except Exception as e:
                logger.warning("Background extraction failed for %s: %s", rid, e)

        await run_in_threadpool(_run)

    asyncio.create_task(
        _extract_bg(
            record["id"], str(resume_store.get(_USER, record["id"])["file_path"])
        )
    )
    return JSONResponse({"ok": True, **record})


@router.get("")
async def api_resumes_list() -> JSONResponse:
    """List all stored resumes for the current user."""
    resumes = resume_store.list_all(_USER)
    return JSONResponse({"ok": True, "resumes": resumes})


@router.delete("/{resume_id}")
async def api_resumes_delete(resume_id: str) -> JSONResponse:
    deleted = resume_store.delete(_USER, resume_id)
    if not deleted:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.get("/{resume_id}/file")
async def api_resumes_file(resume_id: str) -> FileResponse:
    """Serve the raw file for preview."""
    row = resume_store.get(_USER, resume_id)
    if not row or not os.path.exists(row["file_path"]):
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return FileResponse(row["file_path"], media_type=row["mime_type"])


@router.post("/{resume_id}/label")
async def api_resumes_label(resume_id: str, request: Request) -> JSONResponse:
    body = await request.json()
    label = (body.get("label") or "").strip()
    if not label:
        return JSONResponse({"ok": False, "error": "label required"}, status_code=400)
    resume_store.set_label(_USER, resume_id, label)
    return JSONResponse({"ok": True})


@router.post("/{resume_id}/use-for-matching")
async def api_resumes_use_for_matching(resume_id: str) -> JSONResponse:
    """Load a stored resume into the job-matching session so Job Matches uses it."""
    row = resume_store.get(_USER, resume_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    extracted = row.get("extracted_json")
    if not extracted:
        return JSONResponse(
            {"ok": False, "error": "not_extracted_yet"}, status_code=400
        )

    if session.get_resume_id() == resume_id:
        name = row.get("label") or row.get("original_name", "Resume")
        logger.info("Resume '%s' already active - returning stored scores", name)
        return JSONResponse({"ok": True, "rescored": 0, "cached": True})

    resume_json = _json.loads(extracted)
    name = row.get("label") or row.get("original_name", "Resume")
    session.set_resume(resume_json, name, resume_id=resume_id)
    rescored = await run_in_threadpool(rescore_all)
    return JSONResponse({"ok": True, "rescored": rescored, "cached": False})


@router.post("/recommend")
async def api_resumes_recommend(request: Request) -> JSONResponse:
    """Score all cached resumes against a JD and return ranked results."""
    body = await request.json()
    jd_text = (body.get("jd") or "").strip()

    if len(jd_text) < 100:
        return JSONResponse({"ok": False, "error": "jd too short"}, status_code=400)

    scoreable = resume_store.list_scoreable(_USER)
    if len(scoreable) < 2:
        return JSONResponse({"ok": True, "scores": [], "recommended_id": None})

    def _score():
        try:
            jd_json = extract_jd(jd_text)
        except Exception as e:
            logger.warning("JD extraction failed in recommend: %s", e)
            return None
        if not jd_json:
            return None
        results = []
        for r in scoreable:
            try:
                resume_json = _json.loads(r["extracted_json"])
                result = match(resume_json, jd_json)
                results.append(
                    {
                        "id": r["id"],
                        "label": r["label"],
                        "name": r["original_name"],
                        "score": round(result.get("overall_score", 0)),
                    }
                )
            except Exception as e:
                logger.warning("Scoring failed for resume %s: %s", r["id"], e)
        return sorted(results, key=lambda x: x["score"], reverse=True)

    scores = await run_in_threadpool(_score)
    if scores is None:
        return JSONResponse(
            {"ok": False, "error": "could not parse JD"}, status_code=422
        )

    return JSONResponse(
        {
            "ok": True,
            "scores": scores,
            "recommended_id": scores[0]["id"] if scores else None,
        }
    )
