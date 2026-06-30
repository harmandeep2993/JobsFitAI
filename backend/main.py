# main.py
"""
Application entry point for JobsFitAI.

Responsibilities:
- Serve the static frontend (templates/index.html + assets/)
- Register all API routers
- Run background auto-fetch scheduler
- Start the FastAPI/uvicorn server
"""

import asyncio
import hmac as _hmac
import json as _json
import os
import secrets as _secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core import database as db, state as session
from core.security import validate_secret
from core.config import (
    MAX_FILE_SIZE_MB,
    SEARCH_PER_TITLE,
    SUPPORTED_EXTENSIONS,
)
from core.logger import get_logger
from repositories import resume_repo as resume_store
from repositories import settings_repo as settings_store
from services.job_matcher import (
    discover_and_score,
    fetch_combined,
    get_run_status,
)

logger = get_logger("main")

# ---------------------------------------------------------------------------
# Mutable scheduler-state container -- exported so api/routes/matches.py can
# reset it when the user enables the scheduler via the settings panel.
# ---------------------------------------------------------------------------
_sched_last_ref: list[float] = [0.0]

app = FastAPI(title="JobsFitAI")

# templates/ and assets/ live one level up, at the repo root (sibling of backend/).
_ROOT_DIR = Path(__file__).parent.parent

# Static assets
app.mount("/assets", StaticFiles(directory=str(_ROOT_DIR / "assets")), name="assets")


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

# High-frequency poll endpoints logged at DEBUG to avoid console spam.
_POLL_PATHS = {"/api/match/state", "/api/resumes", "/api/llm-ping"}


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    """Log each /api/* and /health request with a short request ID and duration."""
    path = request.url.path
    if path.startswith("/api/") or path == "/health":
        req_id = uuid.uuid4().hex[:8]
        request.state.req_id = req_id
        method = request.method
        _log = logger.debug if path in _POLL_PATHS else logger.info
        _log("[%s] --> %s %s", req_id, method, path)
        t0 = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - t0) * 1000)
        _log(
            "[%s] <-- %s %s %s (%dms)",
            req_id,
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response
    return await call_next(request)


# ---------------------------------------------------------------------------
# Auth middleware (opt-in: only active when APP_PASSWORD is set in .env)
# ---------------------------------------------------------------------------

_AUTH_ENABLED = bool(os.getenv("APP_PASSWORD", "").strip())
_AUTH_USER = os.getenv("APP_USERNAME", "admin").strip()
_AUTH_PASS = os.getenv("APP_PASSWORD", "").strip()
_SESSION_SECRET = os.getenv("SESSION_SECRET") or _secrets.token_hex(32)
_SESSION_COOKIE = "jfai_sess"
_LOGIN_HTML = (_ROOT_DIR / "templates" / "login.html").read_text(encoding="utf-8")

_OPEN_PATHS = {"/login", "/logout"}


# Stateless session tokens: no database needed.
# Token = "username:HMAC(secret, username)" stored in a cookie.
# _make_token() creates one on login; _verify_token() checks it on every request.
# If SESSION_SECRET changes (or server restarts without a fixed secret), all existing
# tokens become invalid and users are logged out -- that is intentional.
def _make_token() -> str:
    sig = _hmac.new(_SESSION_SECRET.encode(), _AUTH_USER.encode(), "sha256").hexdigest()
    return f"{_AUTH_USER}:{sig}"


def _verify_token(token: str) -> bool:
    if not token:
        return False
    try:
        user, sig = token.rsplit(":", 1)
        expected = _hmac.new(
            _SESSION_SECRET.encode(), user.encode(), "sha256"
        ).hexdigest()
        return _hmac.compare_digest(sig, expected) and _hmac.compare_digest(
            user, _AUTH_USER
        )
    except Exception:
        return False


@app.middleware("http")
async def _auth_guard(request: Request, call_next):
    if not _AUTH_ENABLED:
        return await call_next(request)
    path = request.url.path
    if path in _OPEN_PATHS or path.startswith("/assets/"):
        return await call_next(request)
    if not _verify_token(request.cookies.get(_SESSION_COOKIE, "")):
        if path.startswith("/api/") or path == "/health":
            return JSONResponse(
                {"ok": False, "error": "unauthenticated"}, status_code=401
            )
        return RedirectResponse("/login", status_code=302)
    return await call_next(request)


@app.get("/login")
async def login_page(error: str = ""):
    body = _LOGIN_HTML.replace(
        "{ERROR_HTML}",
        '<div class="lc-err">Invalid username or password.</div>' if error else "",
    )
    return HTMLResponse(body)


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = str(form.get("password") or "")
    ok = _AUTH_ENABLED and (
        _hmac.compare_digest(username, _AUTH_USER)
        and _hmac.compare_digest(password, _AUTH_PASS)
    )
    if not ok:
        return RedirectResponse("/login?error=1", status_code=302)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(
        _SESSION_COOKIE,
        _make_token(),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(_SESSION_COOKIE)
    return resp


# ---------------------------------------------------------------------------
# Config constants mirrored for validation
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: Set[str] = SUPPORTED_EXTENSIONS
MAX_FILE_MB: int = MAX_FILE_SIZE_MB


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


@app.get("/")
async def index() -> HTMLResponse:
    with open(_ROOT_DIR / "templates" / "index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

from api.routes import (  # noqa: E402
    auth,
    resume_analyzer,
    ats_maker,
    history,
    resume_improve,
    job_matches,
    resumes,
    settings,
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(resumes.router, prefix="/api/resumes")
app.include_router(resume_analyzer.router, prefix="/api")
app.include_router(job_matches.router, prefix="/api/match")
app.include_router(ats_maker.router, prefix="/api/ats")
app.include_router(resume_improve.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


# ---------------------------------------------------------------------------
# Background scheduler
# ---------------------------------------------------------------------------


async def _auto_fetch_loop() -> None:
    while True:
        await asyncio.sleep(30)
        try:
            if not settings_store.get_scheduler_enabled():
                continue
            interval = settings_store.get_scheduler_interval() * 60
            if (
                _sched_last_ref[0]
                and (time.monotonic() - _sched_last_ref[0]) < interval
            ):
                continue
            if not session.has_resume() or get_run_status()["running"]:
                continue

            _sched_last_ref[0] = time.monotonic()

            def _run() -> dict:
                jobs = fetch_combined(
                    settings_store.get_titles(),
                    location=settings_store.get_location(),
                    countries=settings_store.get_countries(),
                    per_title=SEARCH_PER_TITLE,
                    arbeitnow_limit=settings_store.get_arbeitnow_limit(),
                    bundesagentur_limit=settings_store.get_bundesagentur_limit(),
                )
                return discover_and_score(
                    jobs, entry_only=settings_store.get_entry_only()
                )

            out = await run_in_threadpool(_run)
            logger.info(
                "[scheduler] auto-fetch: %d checked, %d scored",
                out.get("checked", 0),
                out.get("scored", 0),
            )
        except Exception as e:
            logger.error("[scheduler] error: %s", e)


_USER = "local"


async def _backfill_extractions() -> None:
    """Extract resume JSON for any stored resumes that were uploaded before caching was added."""
    from services.extractors.resume_extractor import extract_resume
    from services.parsers import extract_all_text

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
    import logging as _logging

    # Uvicorn re-initialises its own loggers after our logger.py setup runs,
    # restoring the access log to INFO. Re-silence it here so requests are not
    # printed twice (our middleware already covers /api/* with richer context).
    _logging.getLogger("uvicorn.access").setLevel(_logging.WARNING)
    _logging.getLogger("uvicorn.access").propagate = False

    # Seed _sched_last_ref from the last run event so server restarts don't
    # trigger an immediate re-fetch when the interval hasn't elapsed yet.
    with db.connect() as conn:
        row = conn.execute(
            "SELECT created_at FROM events WHERE type='run' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row:
        try:
            last_ts = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last_ts).total_seconds()
            _sched_last_ref[0] = time.monotonic() - elapsed
        except Exception:
            pass

    validate_secret()
    asyncio.create_task(_auto_fetch_loop())
    asyncio.create_task(_backfill_extractions())
    logger.info(
        "[scheduler] loop started (enabled=%s, every %s min)",
        settings_store.get_scheduler_enabled(),
        settings_store.get_scheduler_interval(),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
            f"           Windows : taskkill /F /IM python.exe\n"
            f"           macOS/Linux: kill $(lsof -ti tcp:{PORT})\n"
        )
        sys.exit(1)

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
