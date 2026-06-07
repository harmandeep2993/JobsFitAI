# src/utils/providers/openai.py
# OpenAI API provider

import os
import requests

from src.utils.config import LLM_TEMPERATURE, LLM_MAX_OUTPUT_TOKENS, LLM_TIMEOUT, OPENAI_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Safe to load at module level — config.py import above ensures
# load_dotenv() has already run before this line executes
_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
_MODEL   = OPENAI_CONFIG.get("model", "gpt-4o-mini")


def check() -> bool:
    """
    Check if OpenAI API key is configured and valid.

    Returns:
        bool: True if API key is set and reachable
    """
    if not _API_KEY:
        logger.warning("[OpenAI] No API key found — set OPENAI_API_KEY in .env")
        return False
    
    try:
        r = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {_API_KEY}"},
            timeout=5,
        )
        return r.status_code == 200
    
    except Exception as e:
        logger.error("[OpenAI] Connectivity check failed: %s", e)
        return False


def call(prompt, model: str | None = None):
    """
    Send prompt to OpenAI and return response.

    Args:
        prompt (str): Prompt text
        model (str | None): Model id to use; falls back to the config default.

    Returns:
        str: Response text or None if failed
    """
    if not _API_KEY:
        logger.warning("[OpenAI] No API key set found — set OPENAI_API_KEY in .env")
        return None

    use_model = model or _MODEL

    try:
        response = requests.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       use_model,
                "messages":    [{"role": "user", "content": prompt}],
                "temperature": LLM_TEMPERATURE,
                "max_tokens":  LLM_MAX_OUTPUT_TOKENS,
            },
            timeout=LLM_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        logger.error("[OpenAI] error %s: %s", response.status_code, response.text[:200])
        return None

    except Exception as e:
        logger.error("[OpenAI] call() failed: %s", e)
        return None