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

import collections
import json
import random
import re
import threading
import time
from dataclasses import dataclass

from src.utils import session
from src.utils.config import GROQ_CONFIG, LLM_MAX_OUTPUT_TOKENS
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("LLM Router initialized with %s provider", session.get_provider())

# --- Character/token estimate ---
# Rough English average: 4 chars per token. Used only for Groq TPM pacing;
# NOT used to cap prompts (each provider has its own large context window).
_CHARS_PER_TOKEN = 4

# --- Retry constants ---
_MAX_ATTEMPTS = 4
_BASE_BACKOFF = 1.0  # seconds; doubles each attempt: 1s, 2s, 4s, 8s

# Groq fallback model -- cheap, 128k context, good for degraded-mode calls
_GROQ_FALLBACK_MODEL = GROQ_CONFIG.get("model", "llama-3.1-8b-instant")

# Groq tokens-per-minute rate limit (free tier default from config).
# This is NOT a per-call context limit -- Groq supports 128k tokens per call.
# It is a rolling rate limit: the API returns 429 when you exceed this many
# estimated tokens in any 60-second window. We pace proactively to avoid it.
_GROQ_TPM_LIMIT: int = int(GROQ_CONFIG.get("tpm_limit", 6000))

# Sliding window: deque of (monotonic_timestamp, estimated_tokens) tuples.
# Protected by _groq_lock for thread safety across concurrent requests.
_groq_window: collections.deque = collections.deque()
_groq_lock = threading.Lock()


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

    text: str | None
    provider_used: str
    attempts: int
    degraded: bool


def _groq_pace(prompt: str) -> None:
    """Block until there is enough Groq TPM headroom to send this prompt.

    Groq enforces a tokens-per-minute rate limit at the account level.
    Rather than relying solely on 429 retries (which waste a round-trip),
    we track estimated token spend in a 60-second sliding window and sleep
    proactively when near the limit.

    Estimated tokens = prompt tokens (chars/4) + max_output_tokens (worst-case).
    The lock is released before sleeping so other threads are not blocked.
    """
    estimated = len(prompt) // _CHARS_PER_TOKEN + LLM_MAX_OUTPUT_TOKENS

    while True:
        sleep_secs = 0.0
        with _groq_lock:
            now = time.monotonic()
            # Drop entries that have aged out of the 60-second window
            while _groq_window and _groq_window[0][0] < now - 60.0:
                _groq_window.popleft()

            tokens_in_window = sum(t for _, t in _groq_window)

            if tokens_in_window + estimated <= _GROQ_TPM_LIMIT:
                # Enough headroom -- record this call and proceed
                _groq_window.append((now, estimated))
                return

            # Calculate how long until the oldest entry expires
            if _groq_window:
                oldest_ts = _groq_window[0][0]
                sleep_secs = max((oldest_ts + 60.0) - now + 0.5, 0.1)
            else:
                sleep_secs = 1.0

        # Sleep OUTSIDE the lock so other threads can proceed
        logger.info(
            "Groq TPM pacing: %d/%d tokens in window, need %d more - sleeping %.1fs",
            tokens_in_window,
            _GROQ_TPM_LIMIT,
            estimated,
            sleep_secs,
        )
        time.sleep(sleep_secs)


def _backoff(attempt: int) -> None:
    """Sleep before a retry using exponential backoff with random jitter.

    Attempt 1 -> ~1s, attempt 2 -> ~2s, attempt 3 -> ~4s.
    Jitter (0-1s) avoids thundering-herd when multiple workers retry together.
    """
    delay = min(_BASE_BACKOFF * (2 ** (attempt - 1)), 8.0) + random.random()
    logger.debug("Retry backoff %.1fs (attempt %d/%d)", delay, attempt, _MAX_ATTEMPTS)
    time.sleep(delay)


def _call_with_retry(
    provider_module, prompt: str, model: str
) -> tuple[str | None, int]:
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
                attempt,
                _MAX_ATTEMPTS,
            )
            _backoff(attempt)
        else:
            logger.error("Provider exhausted all %d retry attempts", _MAX_ATTEMPTS)
    return None, _MAX_ATTEMPTS


def _get_provider():
    """Load the provider module for the currently active provider."""
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
    """Check if the active LLM provider is available."""
    provider = _get_provider()
    logger.debug("Checking %s provider connectivity...", session.get_provider())
    return provider.check()


def call_llm(prompt: str) -> "LLMResult | None":
    """
    Send prompt to the active LLM provider, with retry-backoff and Groq fallback.

    Flow:
    1. If the primary provider is Groq, pace the call against the TPM rate limit.
    2. Try the primary provider up to _MAX_ATTEMPTS times with exponential backoff.
    3. If primary exhausts all retries, fall through to Groq as cheap fallback
       (unless primary IS Groq -- no point falling back to yourself).
    4. If Groq also fails, return a degraded LLMResult with text=None rather
       than raising an exception. The caller decides how to handle degradation.

    No blanket prompt truncation is applied -- each provider has its own
    large context window (OpenAI gpt-4o-mini: 128k, Groq llama-3.1-8b: 128k,
    Ollama: model-dependent). Callers that build very large prompts should trim
    at the call site with domain-specific knowledge about what to keep.

    Groq calls (both primary and fallback) are paced against the tokens-per-minute
    rate limit before sending, so rapid successive calls sleep automatically
    rather than burning 429 round-trips.

    Args:
        prompt (str): Prompt text

    Returns:
        LLMResult | None: Typed result. Check result.degraded and result.text
                          before using the response.
    """
    provider = _get_provider()
    provider_name = session.get_provider()
    model = session.get_model()

    logger.debug(
        "Calling %s (%s) - prompt %d chars",
        provider_name,
        model,
        len(prompt),
    )

    # Pace Groq calls to avoid hitting the tokens-per-minute rate limit
    if provider_name == "groq":
        _groq_pace(prompt)

    # --- Primary provider attempt ---
    text, primary_attempts = _call_with_retry(provider, prompt, model)

    if text is not None:
        logger.info(
            "LLM: %s/%s -> %d chars (%d attempt%s)",
            provider_name,
            model,
            len(text),
            primary_attempts,
            "s" if primary_attempts != 1 else "",
        )
        return LLMResult(
            text=text,
            provider_used=provider_name,
            attempts=primary_attempts,
            degraded=False,
        )

    logger.warning(
        "Primary provider '%s' failed after %d attempts - trying Groq fallback",
        provider_name,
        primary_attempts,
    )

    # --- Groq fallback ---
    # Skip if primary is already Groq -- retrying the same provider gains nothing.
    if provider_name == "groq":
        logger.error("Primary IS Groq and it failed - no further fallback available")
        return LLMResult(
            text=None,
            provider_used="none",
            attempts=primary_attempts,
            degraded=True,
        )

    # Import Groq here (not at module top) to avoid circular-import issues and
    # to keep the normal hot path free of unnecessary imports.
    from src.utils.providers import groq as _groq_mod

    # Pace before the fallback Groq call too
    _groq_pace(prompt)

    groq_text, groq_attempts = _call_with_retry(_groq_mod, prompt, _GROQ_FALLBACK_MODEL)
    total_attempts = primary_attempts + groq_attempts

    if groq_text is not None:
        logger.info(
            "LLM: groq/%s -> %d chars [fallback, %d total attempt%s]",
            _GROQ_FALLBACK_MODEL,
            len(groq_text),
            total_attempts,
            "s" if total_attempts != 1 else "",
        )
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
