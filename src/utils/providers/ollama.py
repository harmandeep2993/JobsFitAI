# src/utils/providers/ollama.py
"""
Ollama local LLM provider for JobsFitAI.
Runs fully local - no API key required. Get Ollama: https://ollama.com
"""

import requests

from src.utils.config import (
    LLM_MAX_OUTPUT_TOKENS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_CONFIG,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

OLLAMA_URL = OLLAMA_CONFIG.get("url", "http://localhost:11434/api/generate")
OLLAMA_HEALTH_URL = OLLAMA_CONFIG.get("health_url", "http://localhost:11434")
_MODEL = OLLAMA_CONFIG.get("model", "qwen2.5:3b")


def check() -> bool:
    """
    Check if a local Ollama server is running.

    Returns:
        bool: True if reachable
    """
    try:
        r = requests.get(OLLAMA_HEALTH_URL, timeout=3)
        return r.status_code == 200
    except Exception as e:
        logger.error("[Ollama] Connectivity check failed: %s", e)
        return False


def call(prompt: str, model: str | None = None) -> str | None:
    """
    Send prompt to Ollama and return response text.

    Args:
        prompt (str): Prompt text
        model (str | None): Model id to use; falls back to the config default.

    Returns:
        str | None: Response text or None if failed
    """
    use_model = model or _MODEL

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": use_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_OUTPUT_TOKENS,
                },
            },
            timeout=LLM_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()["response"].strip()

        logger.error("[Ollama] Error %s: %s", response.status_code, response.text[:200])
        return None

    except Exception as e:
        logger.error("[Ollama] call() failed: %s", e)
        return None
