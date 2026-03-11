# src/extractors/jd.py

"""
Job Description extraction module. Uses an LLM to extract structured requirements from a job description.
Includes light post-processing to normalize skills and languages.
"""

import re
from src.utils.router import call_llm, parse_json_response
from src.utils.config import JD_MAX_CHARS
from src.extractors.prompts import jd_prompt


def extract_jd(jd_text: str) -> dict:
    """
    Extract structured requirements from job description.

    Args:
        jd_text (str): Raw job description text

    Returns:
        dict: Structured JD Data
    """
    default = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "required_years_experience": 0,
        "required_education": {"degree": "","field":  "",},
        "required_languages": [],
        "responsibilities": [],
        "nice_to_have": [],
    }

    if not jd_text:
        return default
    
    # limit text length
    content = jd_text[:JD_MAX_CHARS]

    response = call_llm(jd_prompt(content))
    result = parse_json_response(response)
    
    if not isinstance(result, dict):
        return default

    # Ensure missing keys are filled
    for key, value in default.items():
        result.setdefault(key, value)
 
    # Normalize required skills
    result["required_skills"] = [ s.lower().strip() for s in result.get("required_skills", []) if s]

    # Expand compound preferred skills
    # e.g. "actuarial (reserving, pricing)" → ["actuarial", "reserving", "pricing"]

    expanded = []

    for skill in result.get("preferred_skills", []):
        clean = re.sub(r"\(.*?\)", "", skill).strip()

        if clean:
            expanded.append(clean.lower())

        for item in re.findall(r"\((.*?)\)", skill):
            for s in item.split(","):
                s = s.strip().lower()
                if s and len(s) > 2:
                    expanded.append(s)

    # Remove duplicates while preserving order
    seen = set()
    normalized = []

    for s in expanded:
        if s not in seen:
            normalized.append(s)
            seen.add(s)

    result["preferred_skills"] = normalized

    # Normalize languages
    result["required_languages"] = [ s.lower().strip() for s in result.get("required_languages", []) if s]

    return result