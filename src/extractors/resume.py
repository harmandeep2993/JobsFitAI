# src/extractors/resume.py
"""
Resume extraction module.

Uses an LLM to extract structured information from resume text.
Includes light post-processing to normalize all string values to lowercase.
"""

from src.utils.router import call_llm, parse_json_response
from src.utils.config import RESUME_MAX_CHARS
from src.prompts import get_resume_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _lowercase_all(data):
    """
    Recursively convert all string values in a nested structure to lowercase.

    Args:
        data: dict, list, or str — any nested combination

    Returns:
        Same structure with all strings lowercased and stripped
    """
    if isinstance(data, str):
        return data.lower().strip()

    elif isinstance(data, list):
        return [_lowercase_all(v) for v in data]

    elif isinstance(data, dict):
        return {k: _lowercase_all(v) for k, v in data.items()}

    else:
        # Preserve numbers, booleans, None — return as-is
        logger.warning("Unexpected type in _lowercase_all: %s", type(data))
        return data


def _is_empty(value) -> bool:
    """
    Check if an extracted field value is considered empty.

    Args:
        value: Any extracted field value

    Returns:
        bool: True if value is empty, False otherwise
    """
    return value in ("", None, [], {}, [""]) or value == [None]


def extract_resume(resume_text: str) -> dict:
    """
    Extract structured resume data from raw text using an LLM.

    Pipeline:
        1. Truncate input to RESUME_MAX_CHARS
        2. Build prompt
        3. Call LLM
        4. Parse JSON response
        5. Normalize all values to lowercase

    Args:
        resume_text (str): Raw resume text

    Returns:
        dict: Structured resume data with all string values lowercased

    Raises:
        ValueError: If LLM response is not a valid dict
    """
    if not resume_text or not resume_text.strip():
        logger.warning("Empty resume text received — returning empty dict")
        return {}

    # Truncate to max allowed chars — safeguard for LLM input limits
    if len(resume_text) > RESUME_MAX_CHARS:
        logger.warning(
            "Resume text truncated from %d to %d characters",
            len(resume_text), RESUME_MAX_CHARS
        )
        resume_text = resume_text[:RESUME_MAX_CHARS]

    prompt   = get_resume_prompt(resume_text)
    response = call_llm(prompt)
    result   = parse_json_response(response)

    if not isinstance(result, dict):
        logger.error("LLM response is not a dict: %s", result)
        raise ValueError("Invalid LLM response format")

    result = _lowercase_all(result)
    logger.info("Resume lowercasing complete")

    # Warn about any empty fields in the extracted result
    empty_keys = [k for k, v in result.items() if _is_empty(v)]
    if empty_keys:
        logger.warning("Empty values for keys: %s", empty_keys)
    else:
        logger.info("All resume fields extracted successfully")

    logger.info("Resume extraction complete")
    return result