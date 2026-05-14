# src/extractors/resume.py

"""
Resume extraction module. Uses LLM prompts to extract structured information from resume text.
Includes factual post-processing helpers to improve reliability.
"""

import re
import datetime as dt

from src.utils.router import call_llm, parse_json_response
from src.utils.config import RESUME_MAX_CHARS
from src.prompts import get_resume_prompt 

from src.utils.logger import get_logger

logger = get_logger(__name__)

today = dt.date.today()


def _lowercase_all(data):
    """
    Recursively convert all string values to lowercase.
    
    Args:
        data: A nested structure (dict, list, or string)

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


def extract_resume(schema_type: str, resume_text: str) -> dict:
    """
    Extract structured resume data using an LLM.

    Args:
        resume_text (str): Raw resume text
        
    Returns:
        dict: Structured resume data
    """

    schema_type = schema_type.lower().strip()
    if schema_type not in ("quick", "detailed"):
        logger.error(f"Invalid schema_type: {schema_type}. Must be 'quick' or 'detailed'.")
        return {}

    # If resume text is empty or only whitespace, return an empty dict
    if not resume_text or not resume_text.strip():
        return {}
    
    # Truncate resume text to max allowed characters to avoid LLM overload
    resume_text = resume_text[:RESUME_MAX_CHARS]
    
    prompt = get_resume_prompt(schema_type, resume_text)
    response = call_llm(prompt)
    result = parse_json_response(response)

    # Validate that the result is a dict before returning
    if not isinstance(result, dict):
        logger.error(f"LLM response is not a dict: {result}")
        return {}
    
    # Normalize all string values to lowercase for consistency
    result = _lowercase_all(result)

    logger.info(f"Extracted resume data!")

    return result


