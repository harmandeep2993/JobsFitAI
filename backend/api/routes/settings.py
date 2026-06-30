# api/routes/settings.py
"""
/api/llm-ping, /api/llm-settings, /health endpoints.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from core import db, session
from core.logger import get_logger
from services.llm.router import check_llm

logger = get_logger(__name__)

router = APIRouter()


@router.get("/llm-ping")
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


@router.get("/llm-settings")
async def api_get_llm_settings() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "providers": session.provider_catalog(),
        }
    )


@router.post("/llm-settings")
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


@router.post("/llm-settings/key")
async def api_set_llm_key(request: Request) -> JSONResponse:
    """Set the API key for a provider at runtime; persists to .env."""
    body = await request.json()
    provider = (body.get("provider") or "").strip()
    api_key = (body.get("api_key") or "").strip()

    if not provider:
        return JSONResponse(
            {"ok": False, "error": "provider required"}, status_code=400
        )
    if not api_key:
        return JSONResponse({"ok": False, "error": "api_key required"}, status_code=400)

    if provider == "openai":
        from services.llm.providers import openai as _op

        _op.set_api_key(api_key)
        env_var = "OPENAI_API_KEY"
        hint = _op.get_key_hint()
    elif provider == "groq":
        from services.llm.providers import groq as _gp

        _gp.set_api_key(api_key)
        env_var = "GROQ_API_KEY"
        hint = _gp.get_key_hint()
    else:
        return JSONResponse(
            {"ok": False, "error": f"key setting not supported for {provider}"},
            status_code=400,
        )

    try:
        from dotenv import set_key as _dotenv_set

        _env_path = Path(__file__).parent.parent.parent / ".env"
        _dotenv_set(str(_env_path), env_var, api_key, quote_mode="never")
    except Exception as e:
        logger.warning("Could not persist API key to .env: %s", e)

    return JSONResponse({"ok": True, "provider": provider, "hint": hint})


@router.get("/health")
async def health() -> JSONResponse:
    """
    Component health check.

    Returns per-component status and overall ok flag.
    Status 200 when all components are ok, 503 when any are not.
    """
    components: dict[str, str] = {}

    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
        components["db"] = "ok"
    except Exception as exc:
        logger.error("Health check - db error: %s", exc)
        components["db"] = "error"

    components["config"] = "ok"

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
