# app.py

"""
Application entry point for JobFitAI.

Responsibilities:
- Expose the resume upload API endpoint
- Register the main NiceGUI page
- Start the NiceGUI server
"""

import os
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Set

from nicegui import ui, app as ngapp
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from src.frontend.handlers import register_page
from src.utils.logger import get_logger

logger = get_logger("app")
from src.utils import session
from src.utils.router import check_llm
from src.parsers import extract_all_text
from src.extractors.resume import extract_resume
from src.services.job_matcher import (
    discover_and_score,
    begin_run,
    end_run,
    get_run_status,
    rescore_all,
    fetch_combined,
)
from src.services import match_store, event_store, vector_store, settings_store
from src.services.summary import generate_summary
from src.utils.config import SEARCH_PER_TITLE, MAX_AGE_DAYS


ngapp.add_static_files("/assets", "assets")

# Set Configuration
# Allowed resume file extensions
ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx"}

# Maximum allowed upload size (MB)
MAX_FILE_MB: int = 5


# Upload API
@ngapp.post("/api/upload")
async def api_upload(request: Request) -> JSONResponse:
    """
    Handle resume file uploads.

    The endpoint receives a multipart/form-data request containing a file
    field named "file". The file is saved to a temporary location so it can
    later be processed by the resume parser.

    Parameters
    ----------
    request : Request
        Starlette request object containing the uploaded file.

    Returns
    -------
    JSONResponse
        JSON payload containing:
        - ok (bool)         : upload status
        - name (str)        : original file name
        - tmp (str)         : temporary file path
        - kb (float)        : file size in kilobytes
        - ext (str)         : file extension
    """

    form = await request.form()
    upload = form.get("file")

    if upload is None:
        return JSONResponse({"ok": False, "error": "no file uploaded"}, status_code=400)

    # Read uploaded  file
    data = await upload.read()
    filename = upload.filename or "resume"
    suffix = Path(filename).suffix.lower()

    # Validate file size
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        return JSONResponse(
            {"ok": False, "error": "file too large"},
            status_code=400,
        )

    # Validate file extension
    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {"ok": False, "error": "unsupported file type"}, status_code=400
        )

    # Save uploaded file to a temporary location
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


# LLM Settings API
@ngapp.get("/api/llm-settings")
async def api_get_llm_settings() -> JSONResponse:
    """
    Return the current LLM selection and the selectable provider catalog.

    Returns
    -------
    JSONResponse
        {"ok": True, "current": {provider, model},
         "providers": [{name, default_model, models[]}, ...]}
    """
    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "providers": session.provider_catalog(),
        }
    )


@ngapp.post("/api/llm-settings")
async def api_set_llm_settings(request: Request) -> JSONResponse:
    """
    Set the active provider and model (in-memory, for this session).

    Body
    ----
    {"provider": str, "model": str}  — empty model uses the provider default.

    Returns
    -------
    JSONResponse
        {"ok": True, "current": {provider, model}, "online": bool} on success,
        or {"ok": False, "error": ...} with status 400 for an invalid provider.
    """
    body = await request.json()
    provider = (body.get("provider") or "").strip()
    model = (body.get("model") or "").strip()

    try:
        session.set_active(provider, model)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

    # Connectivity check against the newly selected provider.
    online = await run_in_threadpool(check_llm)

    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "online": online,
        }
    )


# Job Matches API
@ngapp.post("/api/match/resume")
async def api_match_resume(request: Request) -> JSONResponse:
    """
    Parse + extract an uploaded resume and store it for matching.

    Body: {"tmp": <temp path from /api/upload>, "name": <original filename>}
    """
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
    try:
        if os.path.exists(tmp):
            os.unlink(tmp)
    except OSError:
        pass

    if not resume_json:
        return JSONResponse(
            {"ok": False, "error": "could not parse resume"}, status_code=422
        )

    session.set_resume(resume_json, name)

    # New resume -> re-score existing jobs against it (local embeddings, no tokens).
    rescored = await run_in_threadpool(rescore_all)
    if rescored:
        event_store.log_event("rescore", "", f"{rescored} jobs re-scored vs {name}")

    years = resume_json.get("meta", {}).get("total_experience_years", 0)
    return JSONResponse(
        {"ok": True, "name": name, "experience_years": years, "rescored": rescored}
    )


@ngapp.get("/api/match/run")
async def api_match_run(request: Request) -> JSONResponse:
    """
    Discover target AI/ML roles via Adzuna multi-title search, filter to
    entry-level, and score the resume against any new ones.

    Query params:
        query: optional single-title override (defaults to config target_titles)
        location: location filter
        entry_only: "true"/"false" (default true)

    Returns the full ranked result set plus how many were found/scored.
    """
    if not session.has_resume():
        return JSONResponse(
            {"ok": False, "error": "no_resume", "results": match_store.get_all()},
            status_code=400,
        )

    # Don't start a second run on top of an in-progress one.
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

    # Fire-and-forget: results stream into the DB; the client polls /state.
    asyncio.create_task(_bg())
    return JSONResponse({"ok": True, "started": True})


@ngapp.get("/api/match/state")
async def api_match_state() -> JSONResponse:
    """Return current resume status and the stored ranked matches."""
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


@ngapp.post("/api/match/applied")
async def api_match_applied(request: Request) -> JSONResponse:
    """Mark a stored job as applied / not applied. Body: {id, applied}."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    applied = bool(body.get("applied"))
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.set_applied(job_id, applied)
    if applied:
        event_store.log_event("applied", job_id)
    return JSONResponse({"ok": True, "id": job_id, "applied": applied})


@ngapp.get("/api/match/detail")
async def api_match_detail(request: Request) -> JSONResponse:
    """
    Full analysis for one job: JD, section scores, matched/missing skills,
    a resume snapshot, and an LLM summary (generated lazily on first open,
    then cached).
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


@ngapp.post("/api/match/filters")
async def api_match_filters(request: Request) -> JSONResponse:
    """
    Update editable search settings. Body may include:
      target_titles: [str], countries: [str] or "germany, netherlands", location: str
    """
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


@ngapp.post("/api/match/scheduler")
async def api_match_scheduler(request: Request) -> JSONResponse:
    """Turn the background auto-fetch on/off and set its interval (minutes)."""
    global _sched_last
    body = await request.json()
    if "enabled" in body:
        settings_store.set_scheduler_enabled(bool(body["enabled"]))
        if body.get("enabled"):
            _sched_last = 0.0  # run on the next wake (~30s)
    if "interval" in body:
        settings_store.set_scheduler_interval(int(body["interval"]))
    return JSONResponse(
        {
            "ok": True,
            "enabled": settings_store.get_scheduler_enabled(),
            "interval": settings_store.get_scheduler_interval(),
        }
    )


@ngapp.post("/api/match/delete")
async def api_match_delete(request: Request) -> JSONResponse:
    """Delete a single job and block it from being re-fetched."""
    body = await request.json()
    job_id = (body.get("id") or "").strip()
    if not job_id:
        return JSONResponse({"ok": False, "error": "id required"}, status_code=400)
    match_store.delete(job_id)
    event_store.block(job_id)
    return JSONResponse({"ok": True})


@ngapp.post("/api/match/clear")
async def api_match_clear() -> JSONResponse:
    """Clear all stored matches, seen-jobs, events, and job vectors."""
    match_store.clear()
    event_store.clear()
    vector_store.clear()
    return JSONResponse({"ok": True})


# Background auto-fetch scheduler — runtime-controlled via the UI / settings.
_sched_last = 0.0  # monotonic time of last auto-run (0 = run on next wake)


async def _auto_fetch_loop() -> None:
    """Always running; honors the enabled flag + interval from settings."""
    global _sched_last
    while True:
        await asyncio.sleep(30)  # wake periodically to check settings
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


async def _start_scheduler() -> None:
    asyncio.create_task(_auto_fetch_loop())
    logger.info(
        "[scheduler] loop started (enabled=%s, every %s min)",
        settings_store.get_scheduler_enabled(),
        settings_store.get_scheduler_interval(),
    )


ngapp.on_startup(_start_scheduler)


# Main UI Page
@ui.page("/")
def index():
    """
    Register the main application page.

    The UI layout and logic are implemented inside the frontend module.
    """
    register_page()


# Application Entry Point
PORT = 8080


def _port_in_use(port: int) -> bool:
    """Return True if something is already listening on localhost:port."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ in {"__main__", "__mp_main__"}:
    # Guard against the stale-server trap: if an old instance is still
    # bound to the port, the new one would silently fail to bind and you'd
    # keep hitting old code. Fail loudly instead.
    if _port_in_use(PORT):
        import sys

        print(
            f"\n[JobFitAI] Port {PORT} is already in use — an old server is still running.\n"
            f"           Stop it first, then re-run:\n"
            f"           Windows : taskkill /F /IM python.exe\n"
            f"           macOS/Linux: kill $(lsof -ti tcp:{PORT})\n"
        )
        sys.exit(1)

    ui.run(
        title="JobFitAI", port=PORT, reload=False, favicon="🎯", reconnect_timeout=300
    )
