# src/utils/providers/groq.py
# Groq API provider — fast inference, free tier available
# Get API key: https://console.groq.com
# Recommended model: llama-3.1-8b-instant

import requests

from utils.core.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TIMEOUT,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def check():
    """
    Check if Groq API key is configured and valid.

    Returns:
        bool: True if API key is set and reachable
    """
    if not LLM_API_KEY:
        print("Groq: no API key set")
        return False

    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


def call(prompt):
    """
    Send prompt to Groq and return response.
    Groq uses OpenAI-compatible chat completions API.

    Args:
        prompt (str): Prompt text

    Returns:
        str: Response text or None if failed
    """
    if not LLM_API_KEY:
        print("Groq: no API key set")
        return None

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       LLM_MODEL,
                "messages":    [{"role": "user", "content": prompt}],
                "temperature": LLM_TEMPERATURE,
                "max_tokens":  LLM_MAX_TOKENS,
            },
            timeout=LLM_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        print(f"Groq error {response.status_code}: {response.text[:200]}")
        return None

    except Exception as e:
        print(f"Groq call failed: {e}")
        return None