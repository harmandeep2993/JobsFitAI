# src/extractors/extract.py
"""
Extraction pipeline.

Orchestrates resume and JD extraction in sequence.
Returns structured dicts for both inputs, or empty dicts on failure.
"""

from src.extractors.jd import extract_jd
from src.extractors.resume import extract_resume
from src.utils.logger import get_logger
from src.utils.router import check_llm

logger = get_logger(__name__)


def extract_all(resume_text: str, jd_text: str) -> tuple[dict, dict]:
    """
    Extract structured data from resume and job description.

    Runs both extractors independently - a failure in one does not
    block the other.

    Args:
        resume_text (str): Raw resume text
        jd_text (str): Raw job description text

    Returns:
        tuple[dict, dict]: (resume_json, jd_json)
            Returns ({}, {}) if LLM unavailable or both inputs missing.
            Returns ({}, jd_json) or (resume_json, {}) on partial failure.
    """
    if not check_llm():
        logger.error("LLM provider unavailable - aborting extraction")
        return {}, {}

    if not resume_text or not jd_text:
        logger.error("Missing resume or JD text - aborting extraction")
        return {}, {}

    try:
        resume_json = extract_resume(resume_text)
        logger.info("Resume extraction successful")
    except Exception as e:
        logger.error("Resume extraction failed: %s", e)
        resume_json = {}

    try:
        jd_json = extract_jd(jd_text)
        logger.info("JD extraction successful")
    except Exception as e:
        logger.error("JD extraction failed: %s", e)
        jd_json = {}

    return resume_json, jd_json
