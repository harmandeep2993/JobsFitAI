# src/extractors/pipeline.py

"""
Extraction pipeline. Runs the resume and job description extractors and returns
structured JSON data for both inputs.
"""

from src.utils.router import check_llm
from src.extractors.resume import extract_resume
from src.extractors.jd import extract_jd


def extract_all(resume_text, jd_text):
    """
    Extract structured data from resume and job description.

    Args:
        resume_text (str): Raw resume text
        jd_text (str): Raw job description text

    Returns:
        tuple:
            resume_json (dict): Structured resume data
            jd_json (dict): Structured job description data

        Returns ({}, {}) if extraction fails or LLM is unavailable.
    """

    if not check_llm():
        print("LLM provider is not available.")
        return {}, {}

    if not resume_text or not jd_text:
        print("Missing resume or JD text.")
        return {}, {}

    try:
        resume_json = extract_resume(resume_text)
    except Exception as e:
        print(f"Resume extraction failed: {e}")
        resume_json = {}

    try:
        jd_json = extract_jd(jd_text)
    except Exception as e:
        print(f"JD extraction failed: {e}")
        jd_json = {}

    return resume_json, jd_json