# app.py

"""
Application entry point for JobFitAI.

Responsibilities:
- Expose the resume upload API endpoint
- Register the main NiceGUI page
- Start the NiceGUI server
"""

import tempfile
from pathlib import Path
from typing import Set
from dataclasses import asdict

from nicegui import ui, app as ngapp
from starlette.requests   import Request
from starlette.responses  import JSONResponse
from starlette.concurrency import run_in_threadpool

from src.frontend.handlers import register_page
from src.fetchers import fetch_adzuna_jobs


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


# Main UI Page
@ui.page("/")
def index():
    """
    Register the main application page.

    The UI layout and logic are implemented inside the frontend module.
    """
    register_page()

# Application Entry Point 
if __name__ in {"__main__", "__mp_main__"}:

    ui.run(
        title="JobFitAI",
        port=8080,
        reload=False,
        favicon="🎯",
        reconnect_timeout= 300
    )