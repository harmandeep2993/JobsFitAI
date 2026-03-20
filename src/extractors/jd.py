# src/extractors/jd.py

"""
Job Description extraction module. Uses an LLM to extract structured requirements from a job description.
Includes light post-processing to normalize skills and languages.
"""

import re
from unittest import result
from src.utils.router import call_llm, parse_json_response
from src.utils.config import JD_MAX_CHARS
from src.prompts import get_jd_prompt

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _lowercase_all(data):
    """
    Recursively convert all string values to lowercase.
    
    Args:
        data: A nested structure (dict, list, or string

    Returns:     
        The same structure with all string values lowercased
    """

    if isinstance(data, str):
        return data.lower().strip()

    if isinstance(data, list):
        return [_lowercase_all(v) for v in data]

    if isinstance(data, dict):
        return {k: _lowercase_all(v) for k, v in data.items()}

    logger.warning(f"Unexpected data type in _lowercase_all: {type(data)}")
    return data


def _is_empty(value):
    return value in ("", None, [], {}, [""]) or value == [None]


def extract_jd(jd_text: str) -> dict:
    """
    Extract structured JD data and normalize all values to lowercase.

    Args:
        jd_text (str): Raw job description
        
    Returns:
        dict: Structured JD data with all values in lowercase
    """

    # If JD text is empty or only whitespace, return an empty dict
    if not jd_text or not jd_text.strip():
        return {}
    
    # Truncate JD text to max allowed characters for LLM input i.e 2000 characters. This is a safeguard to prevent excessively long inputs.
    jd_text = jd_text[:JD_MAX_CHARS]

    prompt = get_jd_prompt(jd_text)
    response = call_llm(prompt)
    result = parse_json_response(response)

    # Validate that the result is a dictionary (JSON object)
    if not isinstance(result, dict):
        raise ValueError("Invalid LLM response format")

    # Normalize everything to lowercase
    result = _lowercase_all(result)

    keys_to_check = [k for k, v in result.items() if _is_empty(v)]

    if keys_to_check:
        logger.warning(f"Empty values for keys: {keys_to_check}")
    else:
        logger.info(f"JD completed successfully without empty keys")

    logger.info("JD extraction completed successfully")
    return result