# src/utils/router.py
"""
Unified LLM router for JobsFitAI.
All extractors call call_llm() and check_llm() only.
Never import providers directly outside this file.

The active provider and model are runtime state held in
src/utils/session.py -- change them at runtime (e.g. from the Settings
tab) via session.set_active(). They reset to the config.yaml defaults on
restart.
"""

import re
import json
import time
import random
from dataclasses import dataclass

from src.utils import session
from src.utils.config import LLM_MAX_OUTPUT_TOKENS, GROQ_CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("LLM Router initialized with %s provider", session.get_provider())

# --- Token budget constants ---
# 6000-token hard ceiling is the project-wide rule (prompt + response combined).
# We target 5800 to leave a small safety margin so floating-point estimates
# never accidentally breach the ceiling.
_TOKEN_BUDGET    = 6000
_SAFETY_MARGIN   = 200
_MAX_TOTAL       = _TOKEN_BUDGET - _SAFETY_MARGIN   # 5800
_CHARS_PER_TOKEN = 4    # rough English average; intentionally round DOWN for safety

# --- Retry constants ---
_MAX_ATTEMPTS  = 4
_BASE_BACKOFF  = 1.0   # seconds; doubles each attempt: 1s, 2s, 4s, 8s

# Groq fallback model -- cheap, large context, good for degraded-mode calls
_GROQ_FALLBACK_MODEL = GROQ_CONFIG.get("model", "llama-3.1-8b-instant")


@dataclass
class LLMResult:
    """Typed return value from call_llm().

    Callers should check `result.text is not None` or `not result.degraded`
    before using the response. A degraded result means the LLM could not
    be reached on either the primary provider or the Groq fallback.

    Fields:
        text          -- the raw response string, or None if all providers failed
        provider_used -- which provider ultimately answered (e.g. "openai",
                         "groq", "ollama", "none")
        attempts      -- total provider.call() invocations across all retries
                         and fallback providers combined
        degraded      -- True when we fell back to Groq OR when text is None
    """
    text:          str | None
    provider_used: str
    attempts:      int
    degraded:      bool


def _trim_to_budget(prompt: str) -> str:
    """Truncate prompt so (prompt_tokens + max_output_tokens) stays under _MAX_TOTAL.

    Uses a 4-chars-per-token estimate. Truncates from the END so the
    instruction and the most important context at the top are always preserved.
    Callers should put the most important content first (instructions, then
    document text).
    """
    # How many prompt tokens we can afford given that output tokens will also
    # consume part of the shared budget.
    allowed_prompt_tokens = _MAX_TOTAL - LLM_MAX_OUTPUT_TOKENS
    if allowed_prompt_tokens <= 0:
        # LLM_MAX_OUTPUT_TOKENS is unexpectedly large; give half the budget to
        # the prompt so we still have something useful to send.
        allowed_prompt_tokens = _MAX_TOTAL // 2

    allowed_chars = allowed_prompt_tokens * _CHARS_PER_TOKEN
    if len(prompt) > allowed_chars:
        logger.warning(
            "Prompt trimmed %d -> %d chars to stay under %d-token budget",
            len(prompt), allowed_chars, _TOKEN_BUDGET,
        )
        return prompt[:allowed_chars]
    return prompt


def _backoff(attempt: int) -> None:
    """Sleep before a retry using exponential backoff with random jitter.

    Attempt 1 -> ~1s, attempt 2 -> ~2s, attempt 3 -> ~4s.
    Jitter (0-1s) avoids thundering-herd when multiple workers retry together.
    """
    delay = min(_BASE_BACKOFF * (2 ** (attempt - 1)), 8.0) + random.random()
    logger.debug("Retry backoff %.1fs (attempt %d/%d)", delay, attempt, _MAX_ATTEMPTS)
    time.sleep(delay)


def _call_with_retry(provider_module, prompt: str, model: str) -> tuple[str | None, int]:
    """Call provider.call() up to _MAX_ATTEMPTS times, retrying on None.

    All provider modules catch their own exceptions internally and return None
    on any error (network timeout, HTTP 4xx/5xx, parse error). Treating None
    as a retriable failure here means we automatically retry on rate-limits,
    transient timeouts, and connection errors without needing to inspect the
    specific exception type.

    Returns (text, attempts_used). Returns (None, _MAX_ATTEMPTS) when all
    attempts are exhausted.
    """
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        text = provider_module.call(prompt, model)
        if text is not None:
            return text, attempt
        if attempt < _MAX_ATTEMPTS:
            logger.warning(
                "Provider returned None on attempt %d/%d - retrying",
                attempt, _MAX_ATTEMPTS,
            )
            _backoff(attempt)
        else:
            logger.error("Provider exhausted all %d retry attempts", _MAX_ATTEMPTS)
    return None, _MAX_ATTEMPTS


def _get_provider():
    """
    Load the provider module for the currently active provider.

    Returns:
        module: Provider module with check() and call()
    """
    name = session.get_provider()

    if name == "openai":
        from src.utils.providers import openai
        logger.debug("Using OpenAI provider")
        return openai

    if name == "groq":
        from src.utils.providers import groq
        logger.debug("Using Groq provider")
        return groq

    # Default -- ollama
    from src.utils.providers import ollama
    logger.debug("Using Ollama provider")
    return ollama


def check_llm() -> bool:
    """
    Check if the active LLM provider is available.

    Returns:
        bool: True if provider is reachable
    """
    provider = _get_provider()
    logger.debug("Checking %s provider connectivity...", session.get_provider())
    return provider.check()


def call_llm(prompt: str) -> "LLMResult | None":
    """
    Send prompt to the active LLM provider, with retry-backoff and Groq fallback.

    Flow:
    1. Trim prompt to keep total tokens under the 6000-token ceiling.
    2. Try the primary provider up to _MAX_ATTEMPTS times with backoff.
    3. If primary exhausts all retries, fall through to Groq as cheap fallback
       (unless primary IS Groq -- no point falling back to yourself).
    4. If Groq also fails, return a degraded LLMResult with text=None rather
       than raising an exception. The caller decides how to handle degradation.

    Args:
        prompt (str): Prompt text

    Returns:
        LLMResult | None: Typed result. None only when call_llm itself errors
                          catastrophically (should not happen in normal use).
                          Check result.degraded and result.text before using.
    """
    prompt = _trim_to_budget(prompt)

    provider      = _get_provider()
    provider_name = session.get_provider()
    model         = session.get_model()

    logger.debug(
        "Calling %s (%s) - prompt %d chars",
        provider_name, model, len(prompt),
    )

    # --- Primary provider attempt ---
    text, primary_attempts = _call_with_retry(provider, prompt, model)

    if text is not None:
        return LLMResult(
            text=text,
            provider_used=provider_name,
            attempts=primary_attempts,
            degraded=False,
        )

    logger.warning(
        "Primary provider '%s' failed after %d attempts - trying Groq fallback",
        provider_name, primary_attempts,
    )

    # --- Groq fallback ---
    # Skip if primary is already Groq -- retrying the same provider gains nothing.
    if provider_name == "groq":
        logger.error(
            "Primary IS Groq and it failed - no further fallback available"
        )
        return LLMResult(
            text=None,
            provider_used="none",
            attempts=primary_attempts,
            degraded=True,
        )

    # Import Groq here (not at module top) to avoid circular-import issues and
    # to keep the normal hot path free of unnecessary imports.
    from src.utils.providers import groq as _groq_mod

    groq_text, groq_attempts = _call_with_retry(
        _groq_mod, prompt, _GROQ_FALLBACK_MODEL
    )
    total_attempts = primary_attempts + groq_attempts

    if groq_text is not None:
        logger.info(
            "Groq fallback succeeded after %d total attempts (primary: %d, groq: %d)",
            total_attempts, primary_attempts, groq_attempts,
        )
        # degraded=True because we had to fall back -- callers can log or alert
        # on this if they want to track primary-provider health.
        return LLMResult(
            text=groq_text,
            provider_used="groq",
            attempts=total_attempts,
            degraded=True,
        )

    logger.error(
        "All providers failed (%d total attempts) - returning degraded result",
        total_attempts,
    )
    return LLMResult(
        text=None,
        provider_used="none",
        attempts=total_attempts,
        degraded=True,
    )


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
        logger.warning("Empty response -- cannot parse JSON")
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
