# src/utils/providers/ollama.py
# Ollama local LLM provider

import requests

from utils.core.config import (
    OLLAMA_URL,
    OLLAMA_HEALTH_URL,
    LLM_MODEL,
    LLM_TIMEOUT,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)


def check():
    """Check if Ollama is running."""
    try:
        r = requests.get(OLLAMA_HEALTH_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def call(prompt):
    """
    Send prompt to Ollama and return response.

    Args:
        prompt (str): Prompt text

    Returns:
        str: Response text or None if failed
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model":   LLM_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                },
            },
            timeout=LLM_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()["response"].strip()

        print(f"Ollama error: {response.status_code}")
        return None

    except Exception as e:
        print(f"Ollama call failed: {e}")
        return None