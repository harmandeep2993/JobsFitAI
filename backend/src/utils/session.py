# src/utils/session.py
"""
Runtime LLM selection state.

Holds the currently active provider and (optional) model override chosen
at runtime - e.g. from the Settings tab in the UI. This is in-memory only:
it applies for the life of the running process and resets to the
config.yaml defaults on restart.

The router reads `get_provider()` / `get_model()` on every call, so a
change here takes effect on the next analysis without a restart.
"""

import json
from datetime import datetime, timezone

from src.services import db
from src.utils.config import PROVIDER_CONFIGS
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Providers the router has a working path for.
SUPPORTED_PROVIDERS = ["openai", "groq", "ollama"]

# Default provider used until the user changes it.
# OpenAI gpt-4o-mini has far higher rate limits than Groq's free tier
# (which caps at 6k tokens/min - too small for this 3-call pipeline).
DEFAULT_PROVIDER = "openai"

# model = None means "use this provider's default model from config.yaml".
_state = {
    "provider": DEFAULT_PROVIDER,
    "model": None,
}

# Extracted resume - cached in memory and persisted to SQLite so it
# survives restarts (no re-extraction). "loaded" tracks whether we've
# tried loading from the DB yet.
_resume = {
    "json": None,
    "name": "",
    "id": None,  # resume_id from the resumes table; None for legacy temp uploads
    "loaded": False,
}


def _ensure_resume_loaded() -> None:
    """Lazily load the persisted resume from the DB on first access."""
    if _resume["loaded"]:
        return
    try:
        with db.connect() as conn:
            row = conn.execute("SELECT name, json FROM resume WHERE id = 1").fetchone()
        if row and row["json"]:
            _resume["json"] = json.loads(row["json"])
            _resume["name"] = row["name"] or ""
            logger.info("Loaded persisted resume: %s", _resume["name"] or "(unnamed)")
    except Exception as e:
        logger.error("Failed to load persisted resume: %s", e)
    finally:
        _resume["loaded"] = True


def get_provider() -> str:
    """Return the active provider name."""
    return _state["provider"]


def get_model() -> str:
    """
    Return the active model id.

    Falls back to the provider's default model from config.yaml when no
    explicit override is set.
    """
    if _state["model"]:
        return _state["model"]
    return PROVIDER_CONFIGS.get(_state["provider"], {}).get("model", "")


def set_active(provider: str, model: str | None = None) -> None:
    """
    Set the active provider and optional model override.

    Args:
        provider (str): One of SUPPORTED_PROVIDERS.
        model (str | None): Model id, or empty/None to use the provider default.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = (provider or "").strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider!r}")

    _state["provider"] = provider
    _state["model"] = (model or "").strip() or None

    logger.info("Active LLM set to %s / %s", provider, get_model())


def get_settings() -> dict:
    """Return the current selection as {'provider', 'model'}."""
    return {"provider": get_provider(), "model": get_model()}


def get_resume_id() -> str | None:
    """Return the resume_id of the currently active resume, or None."""
    return _resume["id"]


def set_resume(resume_json: dict, name: str = "", resume_id: str | None = None) -> None:
    """Store the extracted resume (in memory + persisted) for reuse."""
    _resume["json"] = resume_json
    _resume["name"] = name or ""
    _resume["id"] = resume_id
    _resume["loaded"] = True

    try:
        with db.connect() as conn:
            conn.execute(
                """
                INSERT INTO resume (id, name, json, created_at) VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, json=excluded.json, created_at=excluded.created_at
                """,
                (
                    _resume["name"],
                    json.dumps(resume_json),
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
    except Exception as e:
        logger.error("Failed to persist resume: %s", e)

    logger.info("Resume stored for matching: %s", _resume["name"] or "(unnamed)")


def get_resume() -> dict | None:
    """Return the stored resume JSON, or None if none is loaded."""
    _ensure_resume_loaded()
    return _resume["json"]


def get_resume_name() -> str:
    """Return the stored resume's display name."""
    _ensure_resume_loaded()
    return _resume["name"]


def has_resume() -> bool:
    """True if a resume has been extracted and stored."""
    return get_resume() is not None


def _flatten_skills(skills) -> list:
    if isinstance(skills, list):
        return [s for s in skills if isinstance(s, str)]
    if isinstance(skills, dict):
        out = []
        for v in skills.values():
            if isinstance(v, list):
                out.extend(s for s in v if isinstance(s, str))
        return out
    return []


def resume_info() -> dict:
    """Compact view of the stored resume for the dashboard panel."""
    r = get_resume()
    if not r:
        return {}
    return {
        "name": get_resume_name(),
        "title": (r.get("candidate") or {}).get("title", ""),
        "total_years": (r.get("meta") or {}).get("total_experience_years", 0),
        "skills": _flatten_skills(r.get("skills", [])),
        "experience": [
            {
                "title": e.get("title", ""),
                "company": e.get("company", ""),
                "start": e.get("start_date", ""),
                "end": e.get("end_date", ""),
                "years": e.get("duration_years", 0),
            }
            for e in r.get("experience_entries", [])
            if isinstance(e, dict)
        ],
        "education": [
            {
                "degree": e.get("degree", ""),
                "field": e.get("field", ""),
                "institution": e.get("institution", ""),
            }
            for e in r.get("education", [])
            if isinstance(e, dict)
        ],
        "languages": r.get("languages", []),
        "certifications": r.get("certifications", []),
    }


def provider_catalog() -> list[dict]:
    """
    Return the selectable providers for the UI.

    Each entry: {name, default_model, models[], needs_key, has_key, key_hint}.
    """
    from src.utils.providers import groq as _groq_p
    from src.utils.providers import openai as _openai_p

    _meta = {
        "openai": {"needs_key": True, "mod": _openai_p},
        "groq": {"needs_key": True, "mod": _groq_p},
        "ollama": {"needs_key": False, "mod": None},
    }

    catalog = []
    for name in SUPPORTED_PROVIDERS:
        cfg = PROVIDER_CONFIGS.get(name, {})
        meta = _meta.get(name, {})
        mod = meta.get("mod")
        catalog.append(
            {
                "name": name,
                "default_model": cfg.get("model", ""),
                "models": cfg.get("models", []),
                "needs_key": meta.get("needs_key", False),
                "has_key": mod.has_key() if mod else True,
                "key_hint": mod.get_key_hint() if mod else "",
            }
        )
    return catalog
