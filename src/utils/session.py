# src/utils/session.py
"""
Runtime LLM selection state.

Holds the currently active provider and (optional) model override chosen
at runtime — e.g. from the Settings tab in the UI. This is in-memory only:
it applies for the life of the running process and resets to the
config.yaml defaults on restart.

The router reads `get_provider()` / `get_model()` on every call, so a
change here takes effect on the next analysis without a restart.
"""

from src.utils.config import PROVIDER_CONFIGS
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Providers the router has a working path for.
SUPPORTED_PROVIDERS = ["openai", "groq", "ollama"]

# Default provider used until the user changes it.
# OpenAI gpt-4o-mini has far higher rate limits than Groq's free tier
# (which caps at 6k tokens/min — too small for this 3-call pipeline).
DEFAULT_PROVIDER = "openai"

# model = None means "use this provider's default model from config.yaml".
_state = {
    "provider": DEFAULT_PROVIDER,
    "model":    None,
}

# Extracted resume kept in memory so the Job Matches dashboard can score
# many jobs without re-extracting the resume each time.
_resume = {
    "json": None,
    "name": "",
}


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
    _state["model"]    = (model or "").strip() or None

    logger.info("Active LLM set to %s / %s", provider, get_model())


def get_settings() -> dict:
    """Return the current selection as {'provider', 'model'}."""
    return {"provider": get_provider(), "model": get_model()}


def set_resume(resume_json: dict, name: str = "") -> None:
    """Store the extracted resume for reuse by the matching dashboard."""
    _resume["json"] = resume_json
    _resume["name"] = name or ""
    logger.info("Resume stored for matching: %s", _resume["name"] or "(unnamed)")


def get_resume() -> dict | None:
    """Return the stored resume JSON, or None if none is loaded."""
    return _resume["json"]


def get_resume_name() -> str:
    """Return the stored resume's display name."""
    return _resume["name"]


def has_resume() -> bool:
    """True if a resume has been extracted and stored."""
    return bool(_resume["json"])


def provider_catalog() -> list[dict]:
    """
    Return the selectable providers for the UI.

    Each entry: {name, default_model, models[]}.
    """
    catalog = []
    for name in SUPPORTED_PROVIDERS:
        cfg = PROVIDER_CONFIGS.get(name, {})
        catalog.append({
            "name":          name,
            "default_model": cfg.get("model", ""),
            "models":        cfg.get("models", []),
        })
    return catalog
