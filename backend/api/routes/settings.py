# api/routes/settings.py
"""
/api/llm-ping, /api/llm-settings, /health endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.routes.auth import get_current_user, require_admin
from core import database as db, state as session
from core.logger import get_logger
from services.llm.caller import check_llm
from schemas.common import LlmSettingsRequest

logger = get_logger(__name__)

router = APIRouter()


@router.get("/llm-ping")
async def api_llm_ping(
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
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
async def api_get_llm_settings(
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "providers": session.provider_catalog(),
        }
    )


@router.post("/llm-settings")
async def api_set_llm_settings(
    body: LlmSettingsRequest,
    current_user: dict = Depends(require_admin),
) -> JSONResponse:
    """Switch the active LLM provider and/or model; verifies connectivity after switching.

    Admin only - the provider selection is app-wide, so a regular user
    changing it would affect every other user's analyses.
    """
    provider = (body.provider or "").strip()
    model = (body.model or "").strip()

    try:
        session.set_active(provider, model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    online = await run_in_threadpool(check_llm)

    return JSONResponse(
        {
            "ok": True,
            "current": session.get_settings(),
            "online": online,
        }
    )


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
