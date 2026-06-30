# api/routes/resume_analyzer.py
"""
Analyzer endpoints: /api/upload, /api/resume-preview, /api/resume-file, /api/analyze
"""

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Set

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core.config import JD_MAX_CHARS, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from core.logger import get_logger
from services.extractors import extract_all
from frontend.results import build_results_html, render_error_panel
from services.matcher.engine import match
from services.parsers import extract_all_text
from repositories import analysis_repo as analysis_store
from repositories import cache_repo as cache_store
from repositories import resume_repo as resume_store
from services.profile_summary import generate_summary
from services.llm.caller import check_llm

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
async def api_upload(request: Request) -> JSONResponse:
    """
    Handle resume file uploads.

    Returns {ok, name, tmp, kb, ext} on success.
    """
    form = await request.form()
    upload = form.get("file")

    if upload is None:
        return JSONResponse({"ok": False, "error": "no file uploaded"}, status_code=400)

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

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(data)
        temp_path = tmp_file.name

    return JSONResponse(
        {
            "ok": True,
            "name": filename,
            "tmp": temp_path,
            "kb": round(len(data) / 1024, 1),
            "ext": suffix.upper()[1:],
        }
    )


@router.get("/resume-file")
async def api_resume_file(tmp: str) -> FileResponse:
    tmp = tmp.strip()
    if not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
    suffix = Path(tmp).suffix.lower()
    if suffix not in _PREVIEW_TYPES:
        return JSONResponse({"ok": False, "error": "unsupported type"}, status_code=400)
    return FileResponse(tmp, media_type=_PREVIEW_TYPES[suffix])


@router.post("/resume-preview")
async def api_resume_preview(request: Request) -> JSONResponse:
    """Extract raw text from a stored or temp resume file - no LLM, no scoring."""
    body = await request.json()
    tmp = (body.get("tmp") or "").strip()
    resume_id = (body.get("resume_id") or "").strip()

    if resume_id:
        row = resume_store.get(_USER, resume_id)
        if not row or not os.path.exists(row["file_path"]):
            return JSONResponse(
                {"ok": False, "error": "file not found"}, status_code=404
            )
        tmp = row["file_path"]
    elif not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "file not found"}, status_code=400)

    text = await run_in_threadpool(lambda: extract_all_text(tmp))
    if not text:
        return JSONResponse(
            {"ok": False, "error": "could not extract text"}, status_code=422
        )
    return JSONResponse({"ok": True, "text": text[:3000], "total_chars": len(text)})


@router.post("/analyze")
async def api_analyze(request: Request) -> JSONResponse:
    """
    Full analysis pipeline: parse resume -> extract -> score -> summarize.

    Body: {"tmp": <temp path from /api/upload>, "jd": <job description text>}
    Returns: {"ok": true, "score": float, "label": str, "html": str}
    """
    body = await request.json()
    tmp = (body.get("tmp") or "").strip()
    resume_id = (body.get("resume_id") or "").strip()
    jd_text = (body.get("jd") or "").strip()

    if resume_id:
        row = resume_store.get(_USER, resume_id)
        if not row or not os.path.exists(row["file_path"]):
            return JSONResponse(
                {"ok": False, "error": "resume file not found"}, status_code=400
            )
        tmp = row["file_path"]
    elif not tmp or not os.path.exists(tmp):
        return JSONResponse(
            {"ok": False, "error": "resume file not found"}, status_code=400
        )
    if len(jd_text) < 50:
        return JSONResponse(
            {
                "ok": False,
                "error": "jd_too_short",
                "html": render_error_panel(
                    "Job description too short",
                    "Paste the full job description (at least a few sentences). "
                    "Short snippets don't give the analyser enough signal to score accurately.",
                ),
            },
            status_code=400,
        )

    if len(jd_text) > JD_MAX_CHARS:
        logger.warning("JD truncated from %d to %d chars", len(jd_text), JD_MAX_CHARS)
        jd_text = jd_text[:JD_MAX_CHARS]

    cache_key = hashlib.sha256(f"{resume_id or tmp}::{jd_text}".encode()).hexdigest()
    cached = cache_store.get(cache_key)
    if cached:
        logger.info("Cache hit for analysis %s", cache_key[:12])
        return JSONResponse({"ok": True, "cached": True, **cached})

    if not check_llm():
        return JSONResponse({"ok": False, "error": "llm_unavailable"}, status_code=503)

    def _run():
        resume_text = extract_all_text(tmp)
        if not resume_text or len(resume_text) < 50:
            return None, None, None, None

        resume_json, jd_json = extract_all(resume_text, jd_text)
        if not resume_json or not jd_json:
            return resume_json, jd_json, None, None

        results = match(resume_json, jd_json)
        summary = generate_summary(resume_json, jd_json, results)
        return resume_json, jd_json, results, summary

    try:
        resume_json, jd_json, results, summary = await run_in_threadpool(_run)
    except Exception as e:
        logger.error("analyze failed: %s", e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    finally:
        pass  # temp file kept so the same resume can be re-analysed without re-uploading

    if not resume_json and not jd_json:
        return JSONResponse(
            {
                "ok": False,
                "error": "could_not_parse_resume",
                "html": render_error_panel(
                    "Could not read resume",
                    "The file could not be parsed. Make sure it is a valid PDF or DOCX "
                    "with selectable text (not a scanned image). Try re-exporting from your word processor.",
                ),
            },
            status_code=422,
        )
    if not resume_json:
        return JSONResponse(
            {
                "ok": False,
                "error": "resume_extraction_failed",
                "html": render_error_panel(
                    "Resume extraction failed",
                    "The resume text was found but the LLM could not extract structured data. "
                    "Check that your LLM provider is configured and reachable in Settings.",
                ),
            },
            status_code=422,
        )
    if not jd_json:
        return JSONResponse(
            {
                "ok": False,
                "error": "jd_extraction_failed",
                "html": render_error_panel(
                    "Job description extraction failed",
                    "The job description text could not be parsed. Try adding more detail -- "
                    "responsibilities, required skills, and qualifications improve extraction accuracy.",
                ),
            },
            status_code=422,
        )
    if not results:
        return JSONResponse({"ok": False, "error": "scoring_failed"}, status_code=500)

    try:
        html = build_results_html(results, resume_json, jd_json, summary or "")
    except Exception as e:
        logger.error("build_results_html failed: %s", e, exc_info=True)
        return JSONResponse(
            {"ok": False, "error": "results_render_failed"}, status_code=500
        )

    payload = {
        "score": results.get("overall_score", 0),
        "label": results.get("label", ""),
        "html": html,
        "gaps": results.get("missing_required", []),
        "strengths": results.get("matched_required", []),
    }
    cache_store.set(cache_key, payload)

    if resume_id:
        try:
            analysis_store.save(
                resume_id,
                jd_text,
                results.get("overall_score", 0),
                results.get("label", ""),
            )
        except Exception as e:
            logger.error("analysis_store.save failed: %s", e)

    return JSONResponse({"ok": True, "cached": False, **payload})
