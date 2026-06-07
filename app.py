# app.py

"""
Application entry point for JobFitAI.

Responsibilities:
- Expose the resume upload API endpoint
- Register the main NiceGUI page
- Start the NiceGUI server
"""

import os
import tempfile
from pathlib import Path
from typing import Set
from dataclasses import asdict

from nicegui import ui, app as ngapp
from starlette.requests   import Request
from starlette.responses  import JSONResponse
from starlette.concurrency import run_in_threadpool

from src.frontend.handlers import register_page
from src.fetchers import fetch_adzuna_jobs, fetch_arbeitnow_jobs, fetch_adzuna_multi
from src.utils import session
from src.utils.router import check_llm
from src.parsers import extract_all_text
from src.extractors.resume import extract_resume
from src.services.job_matcher import score_new_jobs
from src.services import match_store, role_filter
from src.utils.config import (
    TARGET_TITLES, SEARCH_COUNTRY, SEARCH_PER_TITLE,
    ENTRY_KEYWORDS, EXCLUDE_KEYWORDS, MAX_AGE_DAYS, MAX_EXPERIENCE_YEARS,
)


ngapp.add_static_files('/assets', 'assets')

# Set Configuration
# Allowed resume file extensions
ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".doc"}

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
        return JSONResponse(
            {"ok": False, "error": "no file uploaded"},
            status_code=400
        )
    
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
            {"ok": False, "error": "unsupported file type"},
            status_code=400
        )

    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(data)
        temp_path = tmp_file.name

    return JSONResponse(
        {"ok":   True,
        "name": filename,
        "tmp":  temp_path,
        "kb":   round(len(data) / 1024, 1),
        "ext":  suffix.upper()[1:],
        }
    )

# Job Fetch API
@ngapp.get("/api/fetch-jobs")
async def api_fetch_jobs(request: Request) -> JSONResponse:
    """
    Fetch job postings from Adzuna for a role/location search.

    Query parameters
    ----------------
    query : str
        Role to search for (required).
    location : str
        Location filter (optional).
    results : int
        Number of results to return (1-20, default 8).

    Returns
    -------
    JSONResponse
        {"ok": True, "jobs": [Job, ...]} where each Job is the dataclass
        serialized to a dict (title, company, location, url, description,
        language), or {"ok": False, "error": ...} on failure.
    """
    params   = request.query_params
    query    = (params.get("query") or "").strip()
    location = (params.get("location") or "").strip()

    if not query:
        return JSONResponse(
            {"ok": False, "error": "query is required"},
            status_code=400,
        )

    try:
        results = int(params.get("results", 8))
    except ValueError:
        results = 8
    results = max(1, min(results, 20))

    # fetch_adzuna_jobs is synchronous (uses requests) — run off the event loop.
    jobs = await run_in_threadpool(
        fetch_adzuna_jobs, query, location, results
    )

    return JSONResponse({"ok": True, "jobs": [asdict(job) for job in jobs]})


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
    return JSONResponse({
        "ok":        True,
        "current":   session.get_settings(),
        "providers": session.provider_catalog(),
    })


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
    body     = await request.json()
    provider = (body.get("provider") or "").strip()
    model    = (body.get("model") or "").strip()

    try:
        session.set_active(provider, model)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

    # Connectivity check against the newly selected provider.
    online = await run_in_threadpool(check_llm)

    return JSONResponse({
        "ok":      True,
        "current": session.get_settings(),
        "online":  online,
    })


# Job Matches API
@ngapp.post("/api/match/resume")
async def api_match_resume(request: Request) -> JSONResponse:
    """
    Parse + extract an uploaded resume and store it for matching.

    Body: {"tmp": <temp path from /api/upload>, "name": <original filename>}
    """
    body = await request.json()
    tmp  = (body.get("tmp") or "").strip()
    name = (body.get("name") or "resume").strip()

    if not tmp or not os.path.exists(tmp):
        return JSONResponse({"ok": False, "error": "resume file not found"}, status_code=400)

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
        return JSONResponse({"ok": False, "error": "could not parse resume"}, status_code=422)

    session.set_resume(resume_json, name)
    years = resume_json.get("meta", {}).get("total_experience_years", 0)
    return JSONResponse({"ok": True, "name": name, "experience_years": years})


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

    params     = request.query_params
    query      = (params.get("query") or "").strip()
    location   = (params.get("location") or "").strip()
    entry_only = (params.get("entry_only", "true").lower() != "false")

    titles = [query] if query else TARGET_TITLES

    def _run() -> dict:
        jobs     = fetch_adzuna_multi(titles, location=location,
                                      country=SEARCH_COUNTRY, per_title=SEARCH_PER_TITLE)
        filtered = role_filter.filter_jobs(jobs, entry_only=entry_only, titles=titles)
        outcome  = score_new_jobs(filtered)
        outcome["found"] = len(filtered)
        return outcome

    outcome = await run_in_threadpool(_run)
    return JSONResponse({
        "ok":      True,
        "found":   outcome.get("found", 0),
        "scored":  outcome.get("scored", 0),
        "results": outcome.get("results", []),
    })


@ngapp.get("/api/match/state")
async def api_match_state() -> JSONResponse:
    """Return current resume status and the stored ranked matches."""
    return JSONResponse({
        "ok":          True,
        "has_resume":  session.has_resume(),
        "resume_name": session.get_resume_name(),
        "filters": {
            "target_titles":        TARGET_TITLES,
            "entry_keywords":       ENTRY_KEYWORDS,
            "exclude_keywords":     EXCLUDE_KEYWORDS,
            "max_age_days":         MAX_AGE_DAYS,
            "max_experience_years": MAX_EXPERIENCE_YEARS,
        },
        "results":     match_store.get_all(),
    })


@ngapp.post("/api/match/clear")
async def api_match_clear() -> JSONResponse:
    """Clear all stored matches."""
    match_store.clear()
    return JSONResponse({"ok": True})


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
        title="JobFitAI",
        port=PORT,
        reload=False,
        favicon="🎯",
        reconnect_timeout= 300
    )