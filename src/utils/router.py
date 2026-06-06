# src/utils/router.py
"""
Unified LLM router for JobFitAI.
All extractors call call_llm() and check_llm() only.
Never import providers directly outside this file.

The active provider and model are runtime state held in
src/utils/session.py — change them at runtime (e.g. from the Settings
tab) via session.set_active(). They reset to the config.yaml defaults on
restart.
"""

import re
import json

from src.utils import session
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("LLM Router initialized with %s provider", session.get_provider())


def _get_provider():
    """
    Load the provider module for the currently active provider.

    Returns:
        module: Provider module with check() and call()
    """
    name = session.get_provider()

    if name == "openai":
        from src.utils.providers import openai
        logger.info("Using OpenAI provider")
        return openai

    if name == "groq":
        from src.utils.providers import groq
        logger.info("Using Groq provider")
        return groq

    # Default — ollama
    from src.utils.providers import ollama
    logger.info("Using Ollama provider")
    return ollama


def check_llm() -> bool:
    """
    Check if the active LLM provider is available.

    Returns:
        bool: True if provider is reachable
    """
    provider = _get_provider()
    logger.info("Checking %s provider connectivity...", session.get_provider())
    return provider.check()


def call_llm(prompt: str) -> str | None:
    """
    Send prompt to the active LLM provider using the active model.

    Args:
        prompt (str): Prompt text

    Returns:
        str | None: Response text or None if failed
    """
    provider = _get_provider()
    model    = session.get_model()
    logger.info(
        "Calling %s (%s) with prompt: %s...",
        session.get_provider(), model, prompt[:100]
    )
    return provider.call(prompt, model)


def parse_json_response(response_text: str) -> dict | list | None:
    """
    Safely parse JSON from LLM response.
    Handles markdown fences and extra text around JSON.

    Args:
        response_text (str): Raw LLM response

    Returns:
        dict | list | None: Parsed JSON or None if failed
    """
    if not response_text:
        logger.warning("Empty response — cannot parse JSON")
        return None

    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?", "", response_text).strip()
    clean = re.sub(r"```", "", clean).strip()

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

    logger.warning("Could not parse JSON from LLM response")
    logger.warning("Preview: %s", response_text[:200])
    return None