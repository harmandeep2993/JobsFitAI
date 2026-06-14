# app.py

"""
Application entry point for JobsFitAI.

Responsibilities:
- Serve the static frontend (templates/index.html + assets/)
- Expose all REST API endpoints
- Run background auto-fetch scheduler
- Start the FastAPI/uvicorn server
"""

import asyncio
import csv
import hashlib
import io
import json as _json
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

from fastapi import FastAPI
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from src.utils.logger import get_logger

logger = get_logger("app")

from src.extractors import extract_all
from src.extractors.jd import extract_jd
from src.extractors.resume import extract_resume
from src.frontend.results import build_results_html, render_error_panel
from src.matcher.matcher import match
from src.parsers import extract_all_text
from src.services import (
    analysis_store,
    cache_store,
    db,
    event_store,
    match_store,
    resume_store,
    settings_store,
    vector_store,
)
from src.services.job_matcher import (
    begin_run,
    discover_and_score,
    end_run,
    fetch_combined,
    get_run_status,
    rescore_all,
)
from src.services.summary import generate_summary
from src.utils import session
from src.utils.config import (
    JD_MAX_CHARS,
    MAX_AGE_DAYS,
    MAX_FILE_SIZE_MB,
    SEARCH_PER_TITLE,
    SUPPORTED_EXTENSIONS,
)
from src.utils.router import check_llm

app = FastAPI(title="JobsFitAI")

# Static assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# --- Request logging middleware ---


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    """Log each /api/* and /health request with a short request ID and duration."""
    path = request.url.path
    if path.startswith("/api/") or path == "/health":
        req_id = uuid.uuid4().hex[:8]
        request.state.req_id = req_id
        method = request.method
        logger.info("[%s] --> %s %s", req_id, method, path)
        t0 = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            "[%s] <-- %s %s %s (%dms)",
            req_id,
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response
    return await call_next(request)


# These mirror config.yaml validator block -- sourced at import so Pydantic
# has already validated them before any request arrives.
ALLOWED_EXTENSIONS: Set[str] = SUPPORTED_EXTENSIONS
MAX_FILE_MB: int = MAX_FILE_SIZE_MB


# --- Frontend ---


@app.get("/")
async def index() -> HTMLResponse:
    with open("templates/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/health")
async def health() -> JSONResponse:
    """
    Component health check.

    Returns per-component status and overall ok flag.
    Status 200 when all components are ok, 503 when any are not.
    """
    components: dict[str, str] = {}

    # db
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
        components["db"] = "ok"
    except Exception as exc:
        logger.error("Health check - db error: %s", exc)
        components["db"] = "error"

    # config - Pydantic validated at startup; server would not be running if broken
    components["config"] = "ok"

    # llm
    try:
        reachable = await run_in_threadpool(check_llm)
        components["llm"] = "ok" if reachable else "unreachable"
    except Exception as exc:
        logger.error("Health check - llm error: %s", exc)
        components["llm"] = "error"

    ok = all(v == "ok" for v in components.values())
    return JSONResponse(
        {"ok": ok, "components": components},
        status_code=200 if ok else 503,
    )


# --- Resume upload ---


@app.post("/api/upload")
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


# --- Stored resume endpoints ---

_USER = "local"  # single-user mode; swap for session user_id at launch


@app.post("/api/resumes/upload")
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

    # Extract resume in the background so it's ready for recommendation scoring.
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


@app.get("/api/resumes")
async def api_resumes_list() -> JSONResponse:
    """List all stored resumes for the current user."""
    resumes = resume_store.list_all(_USER)
    return JSONResponse({"ok": True, "resumes": resumes})


@app.delete("/api/resumes/{resume_id}")
async def api_resumes_delete(resume_id: str) -> JSONResponse:
    deleted = resume_store.delete(_USER, resume_id)
    if not deleted:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.get("/api/resumes/{resume_id}/file")
async def api_resumes_file(resume_id: str) -> FileResponse:
    """Serve the raw file for preview."""
    row = resume_store.get(_USER, resume_id)
    if not row or not os.path.exists(row["file_path"]):
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return FileResponse(row["file_path"], media_type=row["mime_type"])


@app.post("/api/resumes/{resume_id}/label")
async def api_resumes_label(resume_id: str, request: Request) -> JSONResponse:
    body = await request.json()
    label = (body.get("label") or "").strip()
    if not label:
        return JSONResponse({"ok": False, "error": "label required"}, status_code=400)
    resume_store.set_label(_USER, resume_id, label)
    return JSONResponse({"ok": True})


@app.post("/api/resumes/{resume_id}/use-for-matching")
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
    resume_json = _json.loads(extracted)
    session.set_resume(
        resume_json, row.get("label") or row.get("original_name", "Resume")
    )
    rescored = await run_in_threadpool(rescore_all)
    return JSONResponse({"ok": True, "rescored": rescored})


@app.post("/api/resumes/recommend")
async def api_resumes_recommend(request: Request) -> JSONResponse:
    """Score all cached resumes against a JD and return ranked results.

    Costs exactly 1 LLM call (extract JD). Resume extraction is pre-cached
    at upload time so no extra LLM calls per resume.
    """
    body = await request.json()
    jd_text = (body.get("jd") or "").strip()

    if len(jd_text) < 100:
        return JSONResponse({"ok": False, "error": "jd too short"}, status_code=400)

    scoreable = resume_store.list_scoreable(_USER)
    if len(scoreable) < 2:
        return JSONResponse({"ok": True, "scores": [], "recommended_id": None})

    def _score():
        jd_json = extract_jd(jd_text)
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


# --- Serve original resume file ---

_PREVIEW_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@app.get("/api/resume-file")
async def api_resume_file(tmp: str) -> FileResponse:
    tmp = tmp.strip()
    if not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "file not found"}, status_code=404)
    suffix = Path(tmp).suffix.lower()
    if suffix not in _PREVIEW_TYPES:
        return JSONResponse({"ok": False, "error": "unsupported type"}, status_code=400)
    return FileResponse(tmp, media_type=_PREVIEW_TYPES[suffix])


# --- Resume text preview (no LLM) ---


@app.post("/api/resume-preview")
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


# --- Analyzer ---


@app.post("/api/analyze")
async def api_analyze(request: Request) -> JSONResponse:
    """
    Full analysis pipeline: parse resume → extract → score → summarize.

    Body: {"tmp": <temp path from /api/upload>, "jd": <job description text>}
    Returns: {"ok": true, "score": float, "label": str, "html": str}
    """
    body = await request.json()
    tmp = (body.get("tmp") or "").strip()
    resume_id = (body.get("resume_id") or "").strip()
    jd_text = (body.get("jd") or "").strip()

    # Resolve file path: stored resume takes priority over temp path.
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

    # Cap JD at the configured limit -- very long JDs are truncated rather than
    # rejected so the user does not need to manually trim before pasting.
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

    # Persist analysis history for stored resumes (non-fatal).
    if resume_id:
        try:
            analysis_store.save(
                resume_id,
                jd_text[:120],
                results.get("overall_score", 0),
                results.get("label", ""),
            )
        except Exception as e:
            logger.error("analysis_store.save failed: %s", e)

    return JSONResponse({"ok": True, "cached": False, **payload})


# --- Resume rewrite ---


@app.post("/api/improve-resume")
async def api_improve_resume(request: Request) -> JSONResponse:
    """
    Generate JD-aligned bullets from all stored resumes.

    Accepts {jd, gaps, strengths}. Pulls extracted JSON from every stored
    resume slot, merges the data, and returns before/after bullet pairs
    grouped by source (Experience, Education, Certifications, Projects).
    """
    from src.services.rewrite import improve_resume

    body = await request.json()
    jd_text = (body.get("jd") or "").strip()
    gaps = body.get("gaps") or []
    strengths = body.get("strengths") or []

    if len(jd_text) < 30:
        return JSONResponse({"ok": False, "error": "jd_required"}, status_code=400)

    jd_json = await run_in_threadpool(extract_jd, jd_text)
    result = await run_in_threadpool(improve_resume, "local", jd_json, gaps, strengths)
    return JSONResponse(result)


# --- ATS Maker ---


@app.post("/api/ats/optimise")
async def api_ats_optimise(request: Request) -> JSONResponse:
    """
    Full ATS resume generation pipeline.

    Accepts {resume_id, jd}. Extracts raw resume text from the stored file,
    checks keyword coverage and structural flags, then calls the LLM once to
    produce a complete ATS-optimised resume (summary, experience, skills,
    education) with exact JD keywords injected verbatim.

    Returns {resume, coverage_before, coverage_after, section_flags,
    formatting_flags, plain_text}.
    """
    from src.services.ats import generate_ats_resume

    body = await request.json()
    resume_id = (body.get("resume_id") or "").strip()
    jd_text = (body.get("jd") or "").strip()

    if not resume_id:
        return JSONResponse(
            {"ok": False, "error": "resume_id_required"}, status_code=400
        )
    if len(jd_text) < 30:
        return JSONResponse({"ok": False, "error": "jd_required"}, status_code=400)

    record = resume_store.get("local", resume_id)
    if not record:
        return JSONResponse({"ok": False, "error": "resume_not_found"}, status_code=404)

    # Extract raw text from file for exact string matching
    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        return JSONResponse(
            {"ok": False, "error": "could_not_read_resume"}, status_code=422
        )

    # Load cached extracted JSON (already done at upload time)
    extracted_raw = record.get("extracted_json")
    if extracted_raw:
        try:
            resume_json = _json.loads(extracted_raw)
        except Exception:
            resume_json = {}
    else:
        resume_json = await run_in_threadpool(extract_resume, resume_text)

    jd_json = await run_in_threadpool(extract_jd, jd_text)

    result = await run_in_threadpool(
        generate_ats_resume, resume_text, resume_json, jd_json
    )
    return JSONResponse({"ok": True, **result})


@app.post("/api/ats/check")
async def api_ats_check(request: Request) -> JSONResponse:
    """
    Lightweight ATS scan - no LLM, no keyword injection.

    Accepts {resume_id}. Returns section heading flags and formatting flags
    only. Fast enough to run on every resume load.
    """
    from src.services.ats import ats_check

    body = await request.json()
    resume_id = (body.get("resume_id") or "").strip()

    if not resume_id:
        return JSONResponse(
            {"ok": False, "error": "resume_id_required"}, status_code=400
        )

    record = resume_store.get("local", resume_id)
    if not record:
        return JSONResponse({"ok": False, "error": "resume_not_found"}, status_code=404)

    resume_text = await run_in_threadpool(extract_all_text, record["file_path"])
    if not resume_text:
        return JSONResponse(
            {"ok": False, "error": "could_not_read_resume"}, status_code=422
        )

    result = await run_in_threadpool(ats_check, resume_text)
    return JSONResponse({"ok": True, **result})


# --- History ---


@app.get("/api/history")
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
            """SELECT e.created_at AS applied_at, m.title, m.company, m.url, m.score, m.label
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


# --- LLM ping ---


@app.get("/api/llm-ping")
async def api_llm_ping() -> JSONResponse:
    """Quick check whether the active LLM provider is reachable."""
    try:
        online = await run_in_threadpool(check_llm)
    except Exception as e:
        logger.error("LLM ping failed: %s", e)
        online = False
    return JSONResponse(
        {"ok": True, "online": online, "current": session.get_settings()}
    )


# --- LLM settings ---


@app.get("/api/llm-settings")
async def api_get_llm_settings() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "providers": session.provider_catalog(),
        }
    )


@app.post("/api/llm-settings")
async def api_set_llm_settings(request: Request) -> JSONResponse:
    """Switch the active LLM provider and/or model; verifies connectivity after switching."""
    body = await request.json()
    provider = (body.get("provider") or "").strip()
    model = (body.get("model") or "").strip()

    try:
        session.set_active(provider, model)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

    online = await run_in_threadpool(check_llm)

    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "online": online,
        }
    )


# --- Resume diff ---


def _resume_diff(old: dict, new: dict) -> dict:
    """Compare two extracted resume dicts and return what changed."""

    def flat_skills(r):
        s = r.get("skills", [])
        if isinstance(s, list):
            return {x.lower().strip() for x in s if isinstance(x, str)}
        if isinstance(s, dict):
            out = set()
            for v in s.values():
                if isinstance(v, list):
                    out.update(x.lower().strip() for x in v if isinstance(x, str))
            return out
        return set()

    old_skills = flat_skills(old)
    new_skills = flat_skills(new)

    old_exp = {
        (e.get("title", "") + "|" + e.get("company", "")).lower()
        for e in old.get("experience_entries", [])
    }
    new_exp = {
        (e.get("title", "") + "|" + e.get("company", "")).lower()
        for e in new.get("experience_entries", [])
    }

    old_yrs = (old.get("meta") or {}).get("total_experience_years", 0)
    new_yrs = (new.get("meta") or {}).get("total_experience_years", 0)

    return {
        "skills_added": sorted(new_skills - old_skills),
        "skills_removed": sorted(old_skills - new_skills),
        "exp_added": sorted(new_exp - old_exp),
        "exp_removed": sorted(old_exp - new_exp),
        "years_before": old_yrs,
        "years_after": new_yrs,
        "languages_before": old.get("languages", []),
        "languages_after": new.get("languages", []),
    }


# --- Job matches ---


@app.post("/api/match/resume")
async def api_match_resume(request: Request) -> JSONResponse:
    """Parse + extract an uploaded resume and store it for matching."""
    body = await request.json()
    tmp = (body.get("tmp") or "").strip()
    name = (body.get("name") or "resume").strip()

    if not tmp or not os.path.exists(tmp):
        return JSONResponse(
            {"ok": False, "error": "resume file not found"}, status_code=400
        )

    def _process() -> dict:
        text = extract_all_text(tmp)
        if not text or len(text) < 50:
            return {}
        return extract_resume(text)

    resume_json = await run_in_threadpool(_process)

    if not resume_json:
        return JSONResponse(
            {"ok": False, "error": "could not parse resume"}, status_code=422
        )

    prev_resume = session.get_resume()
    diff = _resume_diff(prev_resume, resume_json) if prev_resume else None

    session.set_resume(resume_json, name)

    rescored = await run_in_threadpool(rescore_all)
    if rescored:
        event_store.log_event("rescore", "", f"{rescored} jobs re-scored vs {name}")

    years = resume_json.get("meta", {}).get("total_experience_years", 0)
    return JSONResponse(
        {
            "ok": True,
            "name": name,
            "experience_years": years,
            "rescored": rescored,
            "diff": diff,
        }
    )


@app.get("/api/match/run")
async def api_match_run(request: Request) -> JSONResponse:
    """
    Kick off a background job-fetch-and-score run.

    Returns immediately with {started: true} and runs the pipeline in a
    background task. Only one run can be active at a time; subsequent calls
    return {started: false, already_running: true} until the run completes.
    """
    if not session.has_resume():
        return JSONResponse(
            {"ok": False, "error": "no_resume", "results": match_store.get_all()},
            status_code=400,
        )

    if not begin_run():
        return JSONResponse({"ok": True, "started": False, "already_running": True})

    params = request.query_params
    query = (params.get("query") or "").strip()
    entry_only = params.get("entry_only", "true").lower() != "false"
    titles = [query] if query else settings_store.get_titles()
    location = (params.get("location") or "").strip() or settings_store.get_location()
    countries = settings_store.get_countries()

    async def _bg() -> None:
        def _run() -> None:
            jobs = fetch_combined(
                titles,
                location=location,
                countries=countries,
                per_title=SEARCH_PER_TITLE,
            )
            discover_and_score(jobs, entry_only=entry_only)

        try:
            await run_in_threadpool(_run)
        except Exception as e:
            logger.error("match run failed: %s", e)
            end_run()

    asyncio.create_task(_bg())
    return JSONResponse({"ok": True, "started": True})


@app.get("/api/match/state")
async def api_match_state() -> JSONResponse:
    """Full state snapshot polled by the frontend while a run is active."""
    return JSONResponse(
        {
            "ok": True,
            "has_resume": session.has_resume(),
            "resume_name": session.get_resume_name(),
            "filters": {
                "target_titles": settings_store.get_titles(),
                "countries": settings_store.country_names(),
                "location": settings_store.get_location(),
                "max_age_days": MAX_AGE_DAYS,
            },
            "stats": event_store.stats(),
            "run_status": get_run_status(),
            "resume": session.resume_info(),
            "scheduler": {
                "enabled": settings_store.get_scheduler_enabled(),
                "interval": settings_store.get_scheduler_interval(),
            },
            "results": match_store.get_all(),
        }
    )


@app.post("/api/match/applied")
async def api_match_applied(request: Request) -> JSONResponse:
    """Toggle the applied flag on a scored job and log an 'applied' event."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    applied = bool(body.get("applied"))
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.set_applied(job_id, applied)
    if applied:
        event_store.log_event("applied", job_id)
    return JSONResponse({"ok": True, "id": job_id, "applied": applied})


@app.get("/api/match/detail")
async def api_match_detail(request: Request) -> JSONResponse:
    """
    Return full detail for a scored job, lazily generating an LLM summary if absent.

    The summary is generated on first request for a job and then cached in
    the matches table so subsequent calls return immediately.
    """
    job_id = (request.query_params.get("id") or "").strip()
    row = match_store.get_one(job_id)
    if not row:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)

    summary = row.get("summary")
    if not summary and session.has_resume():
        resume_json = session.get_resume()
        results = {
            "overall_score": row.get("score", 0),
            "label": row.get("label", ""),
            "section_scores": row.get("section_scores", {}),
            "matched_required": row.get("matched_required", []),
            "missing_required": row.get("missing_required", []),
            "matched_preferred": [],
            "missing_preferred": [],
        }
        try:
            summary = await run_in_threadpool(
                generate_summary, resume_json, row.get("jd_json", {}), results
            )
            match_store.set_summary(job_id, summary)
        except Exception as e:
            logger.error("summary generation failed: %s", e)
            summary = ""

    return JSONResponse(
        {
            "ok": True,
            "job": {
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "url": row["url"],
                "language": row["language"],
                "posted_at": row["posted_at"],
                "score": row["score"],
                "label": row["label"],
                "applied": row.get("applied", 0),
            },
            "section_scores": row.get("section_scores", {}),
            "matched_required": row.get("matched_required", []),
            "missing_required": row.get("missing_required", []),
            "jd": row.get("jd_json", {}),
            "resume": session.resume_info(),
            "summary": summary or "",
        }
    )


@app.post("/api/match/filters")
async def api_match_filters(request: Request) -> JSONResponse:
    """Update target titles, countries, and/or location filter; returns the new values."""
    body = await request.json()

    if isinstance(body.get("target_titles"), list):
        settings_store.set_titles(body["target_titles"])

    if "countries" in body:
        c = body["countries"]
        names = c if isinstance(c, list) else str(c).replace(",", " ").split()
        settings_store.set_countries(names)

    if "location" in body:
        settings_store.set_location(body.get("location") or "")

    return JSONResponse(
        {
            "ok": True,
            "target_titles": settings_store.get_titles(),
            "countries": settings_store.country_names(),
            "location": settings_store.get_location(),
        }
    )


@app.post("/api/match/score-jd")
async def api_score_jd(request: Request) -> JSONResponse:
    """Score a jd_unavailable job using a manually pasted JD."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    jd_text = (body.get("jd_text") or "").strip()

    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    if len(jd_text) < 50:
        return JSONResponse(
            {"ok": False, "error": "jd_text too short"}, status_code=400
        )
    if not session.has_resume():
        return JSONResponse({"ok": False, "error": "no_resume"}, status_code=400)

    row = match_store.get_one(job_id)
    if not row:
        return JSONResponse({"ok": False, "error": "job not found"}, status_code=404)

    def _score():
        try:
            jd_json = extract_jd(jd_text)
        except Exception as exc:
            logger.warning("extract_jd failed: %s", exc)
            return None, None
        if not jd_json:
            return None, None
        try:
            return jd_json, match(session.get_resume(), jd_json)
        except Exception as exc:
            logger.exception("match() failed in score-jd: %s", exc)
            return None, None

    jd_json, result = await run_in_threadpool(_score)
    if not result:
        return JSONResponse(
            {"ok": False, "error": "could not parse JD"}, status_code=422
        )

    match_store.upsert(
        [
            {
                "id": job_id,
                "source": row["source"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "url": row["url"],
                "language": row["language"],
                "posted_at": row["posted_at"],
                "score": result.get("overall_score", 0),
                "label": result.get("label", ""),
                "matched_required": result.get("matched_required", []),
                "missing_required": result.get("missing_required", []),
                "section_scores": result.get("section_scores", {}),
                "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "jd_json": jd_json,
                "status": "scored",
            }
        ]
    )

    return JSONResponse(
        {
            "ok": True,
            "score": result.get("overall_score", 0),
            "label": result.get("label", ""),
        }
    )


@app.post("/api/match/scheduler")
async def api_match_scheduler(request: Request) -> JSONResponse:
    """Enable/disable the auto-fetch scheduler or change its interval (minutes)."""
    global _sched_last
    body = await request.json()
    if "enabled" in body:
        settings_store.set_scheduler_enabled(bool(body["enabled"]))
        if body.get("enabled"):
            _sched_last = 0.0
    if "interval" in body:
        settings_store.set_scheduler_interval(int(body["interval"]))
    return JSONResponse(
        {
            "ok": True,
            "enabled": settings_store.get_scheduler_enabled(),
            "interval": settings_store.get_scheduler_interval(),
        }
    )


@app.post("/api/match/delete")
async def api_match_delete(request: Request) -> JSONResponse:
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.delete(job_id)
    event_store.block(job_id)
    return JSONResponse({"ok": True})


@app.post("/api/match/clear")
async def api_match_clear() -> JSONResponse:
    match_store.clear()
    event_store.clear()
    vector_store.clear()
    return JSONResponse({"ok": True})


@app.get("/api/match/export")
async def api_match_export() -> StreamingResponse:
    """Download all scored matches as a CSV file."""
    rows = match_store.get_all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "title",
            "company",
            "location",
            "score",
            "label",
            "language",
            "posted_at",
            "applied",
            "url",
        ]
    )
    for r in rows:
        posted = r.get("posted_at") or ""
        if posted and posted.isdigit():
            try:
                posted = datetime.fromtimestamp(int(posted), tz=timezone.utc).strftime(
                    "%Y-%m-%d"
                )
            except (OSError, OverflowError):
                pass
        writer.writerow(
            [
                r.get("title", ""),
                r.get("company", ""),
                r.get("location", ""),
                r.get("score", ""),
                r.get("label", ""),
                r.get("language", ""),
                posted,
                "yes" if r.get("applied") else "no",
                r.get("url", ""),
            ]
        )

    buf.seek(0)
    filename = "jobsfitai_matches.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- Background scheduler ---

_sched_last = 0.0


async def _auto_fetch_loop() -> None:
    global _sched_last
    while True:
        await asyncio.sleep(30)
        try:
            if not settings_store.get_scheduler_enabled():
                continue
            interval = settings_store.get_scheduler_interval() * 60
            if _sched_last and (time.monotonic() - _sched_last) < interval:
                continue
            if not session.has_resume() or get_run_status()["running"]:
                continue

            _sched_last = time.monotonic()

            def _run() -> dict:
                jobs = fetch_combined(
                    settings_store.get_titles(),
                    location=settings_store.get_location(),
                    countries=settings_store.get_countries(),
                    per_title=SEARCH_PER_TITLE,
                )
                return discover_and_score(jobs, entry_only=True)

            out = await run_in_threadpool(_run)
            logger.info(
                "[scheduler] auto-fetch: %d checked, %d scored",
                out.get("checked", 0),
                out.get("scored", 0),
            )
        except Exception as e:
            logger.error("[scheduler] error: %s", e)


async def _backfill_extractions() -> None:
    """Extract resume JSON for any stored resumes that were uploaded before caching was added."""
    resumes = resume_store.list_all(_USER)
    pending = [r for r in resumes if not r.get("extracted_json")]
    if not pending:
        return
    logger.info("[backfill] extracting %d resume(s) without cached JSON", len(pending))

    def _run(r: dict) -> None:
        try:
            text = extract_all_text(r["file_path"])
            if not text or len(text) < 50:
                return
            extracted = extract_resume(text)
            if extracted:
                resume_store.set_extracted(_USER, r["id"], _json.dumps(extracted))
                logger.info("[backfill] done: %s (%s)", r["label"], r["id"])
        except Exception as e:
            logger.warning("[backfill] failed for %s: %s", r["id"], e)

    for r in pending:
        await run_in_threadpool(_run, r)


@app.on_event("startup")
async def _start_scheduler() -> None:
    global _sched_last
    # Seed _sched_last from the last run event so server restarts don't
    # trigger an immediate re-fetch when the interval hasn't elapsed yet.
    with db.connect() as conn:
        row = conn.execute(
            "SELECT created_at FROM events WHERE type='run' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row:
        try:
            last_ts = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last_ts).total_seconds()
            _sched_last = time.monotonic() - elapsed
        except Exception:
            pass

    asyncio.create_task(_auto_fetch_loop())
    asyncio.create_task(_backfill_extractions())
    logger.info(
        "[scheduler] loop started (enabled=%s, every %s min)",
        settings_store.get_scheduler_enabled(),
        settings_store.get_scheduler_interval(),
    )


# --- Entry point ---

PORT = 8080


def _port_in_use(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    import uvicorn

    if _port_in_use(PORT):
        import sys

        print(
            f"\n[JobsFitAI] Port {PORT} is already in use - an old server is still running.\n"
            f"           Stop it first, then re-run:\n"
            f"           Windows    : taskkill /F /IM python.exe\n"
            f"           macOS/Linux: kill $(lsof -ti tcp:{PORT})\n"
        )
        sys.exit(1)

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
