# src/utils/router.py
# Unified LLM router — routes to correct provider
# All extractors call call_llm() and check_llm()
# Never import providers directly outside this file

import re
import json

from src.utils.config import LLM_PROVIDER


def _get_provider():
    """
    Load correct provider module based on config.

    Returns:
        module: Provider module with check() and call()
    """
    if LLM_PROVIDER == "openai":
        from src.utils.providers import openai
        return openai

    if LLM_PROVIDER == "groq":
        from src.utils.providers import groq
        return groq

    # Default — ollama
    from src.utils.providers import ollama
    return ollama


def check_llm():
    """
    Check if configured LLM provider is available.

    Returns:
        bool: True if provider is reachable
    """
    provider = _get_provider()
    return provider.check()


def call_llm(prompt):
    """
    Send prompt to configured LLM provider.

    Args:
        prompt (str): Prompt text

    Returns:
        str: Response text or None if failed
    """
    provider = _get_provider()
    return provider.call(prompt)


def parse_json_response(response_text):
    """
    Safely parse JSON from LLM response.
    Handles markdown fences and extra text around JSON.

    Args:
        response_text (str): Raw LLM response

    Returns:
        dict | list | None: Parsed JSON or None if failed
    """
    if not response_text:
        return None

    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?", "", response_text).strip()

    # Try direct parse first
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Find JSON object in response
    try:
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    # Find JSON array in response
    try:
        match = re.search(r"\[.*\]", clean, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    print("Warning: could not parse JSON from LLM response")
    print(f"Raw response preview: {response_text[:200]}")
    return None