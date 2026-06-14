# src/utils/ollama.py
"""
Thin HTTP wrapper around a locally-running Ollama instance.

These functions are called only from src/utils/router.py via the ollama
provider path. Do not import this module directly from routes or services.
"""

import re
import json
import requests

from src.utils.config import (
    OLLAMA_URL,
    OLLAMA_HEALTH_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
    OLLAMA_MAX_TOKENS,
)


def check_ollama():
    """Check if Ollama is running."""
    try:
        r = requests.get(OLLAMA_HEALTH_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def call_ollama(prompt):
    """
    Send prompt to Ollama and return response.

    Args:
        prompt (str): Prompt to send

    Returns:
        str: Raw response or None if failed
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_predict": OLLAMA_MAX_TOKENS,
                },
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()["response"].strip()
        print(f"Ollama error: {response.status_code}")
        return None
    except Exception as e:
        print(f"Ollama call failed: {e}")
        return None


def parse_json_response(response_text):
    """
    Safely parse JSON from Ollama response.
    Handles extra text or markdown around JSON block.

    Args:
        response_text (str): Raw Ollama response

    Returns:
        dict/list: Parsed JSON or None if failed
    """
    if not response_text:
        return None

    # Try direct parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Find JSON object in response
    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    # Find JSON array in response
    try:
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    print("Warning: could not parse JSON from response")
    print(f"Raw response preview: {response_text[:200]}")
    return None
