# src/utils/router.py
"""
Unified LLM router for JobFitAI.
All extractors call call_llm() and check_llm() only.
Never import providers directly outside this file.

To switch provider — change ACTIVE_PROVIDER below.
"""

import re
import json
import os

from src.utils.config import PROVIDER_CONFIGS
from src.utils.logger import get_logger

logger = get_logger(__name__)


# change this to switch provider
ACTIVE_PROVIDER = "groq"  # openai | groq | ollama

logger.info(f"LLM Router initialized with {ACTIVE_PROVIDER} provider")

def _get_provider():
    """
    Load correct provider module based on ACTIVE_PROVIDER.

    Returns:
        module: Provider module with check() and call()
    """
    if ACTIVE_PROVIDER == "openai":
        from src.utils.providers import openai
        logger.info("Using OpenAI provider")
        return openai

    if ACTIVE_PROVIDER == "groq":
        from src.utils.providers import groq
        logger.info("Using Groq provider")
        return groq

    # Default — ollama
    from src.utils.providers import ollama
    logger.info("Using Ollama provider")
    return ollama


def check_llm() -> bool:
    """
    Check if configured LLM provider is available.

    Returns:
        bool: True if provider is reachable
    """
    provider = _get_provider()
    logger.info(f"Checking {ACTIVE_PROVIDER} provider connectivity...")
    return provider.check()


def call_llm(prompt: str) -> str | None:
    """
    Send prompt to configured LLM provider.

    Args:
        prompt (str): Prompt text

    Returns:
        str | None: Response text or None if failed
    """
    provider = _get_provider()
    logger.info(f"Calling {ACTIVE_PROVIDER} provider with prompt: {prompt[:100]}...")
    return provider.call(prompt)


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