# src/utils/providers/openai.py
# OpenAI API provider

import requests

from src.utils.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TIMEOUT,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def check():
    """
    Check if OpenAI API key is configured and valid.

    Returns:
        bool: True if API key is set and reachable
    """
    if not LLM_API_KEY:
        print("OpenAI: no API key set")
        return False

    try:
        r = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


def call(prompt):
    """
    Send prompt to OpenAI and return response.

    Args:
        prompt (str): Prompt text

    Returns:
        str: Response text or None if failed
    """
    if not LLM_API_KEY:
        print("OpenAI: no API key set")
        return None

    try:
        response = requests.post(
            OPENAI_URL,
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

        print(f"OpenAI error {response.status_code}: {response.text[:200]}")
        return None

    except Exception as e:
        print(f"OpenAI call failed: {e}")
        return None