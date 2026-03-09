# src/extractor/jd.py

import re

from utils.ollama_utils import check_ollama, call_ollama, parse_json_response
from utils.config import JD_MAX_CHARS


def extract_jd(jd_text):
    """
    Extract structured requirements from job description.
    JD is already focused — send full text to LLM.

    Args:
        jd_text (str): Raw job description text

    Returns:
        dict: Structured JD requirements
    """
    default = {
        "job_title":                 "",
        "required_skills":           [],
        "preferred_skills":          [],
        "required_years_experience": 0,
        "required_education": {
            "degree": "",
            "field":  "",
        },
        "required_languages":  [],
        "responsibilities":    [],
        "nice_to_have":        [],
    }

    if not check_ollama():
        print("Warning: Ollama not running")
        return default

    prompt = f"""
Extract all requirements from this job description.
Return ONLY valid JSON. Nothing else.

{{
  "job_title": "exact job title",
  "required_skills": [
    "must have technical skills only"
  ],
  "preferred_skills": [
    "domain knowledge and nice to have skills"
  ],
  "required_years_experience": 0,
  "required_education": {{
    "degree": "masters/bachelors/phd",
    "field": "full field of study"
  }},
  "required_languages": [],
  "responsibilities": [
    "what person will do day to day"
  ],
  "nice_to_have": [
    "bonus qualifications"
  ]
}}

IMPORTANT:
- required_skills: hard technical requirements e.g. Python, R, SQL, AWS etc
- preferred_skills: domain experience, sector knowledge e.g. insurance, actuarial, finance etc
- Split compound skills into individual items e.g. "actuarial (reserving, pricing, risk management)" becomes ["actuarial", "reserving", "pricing", "risk management"] 
- responsibilities: copy exactly from JD
- nice_to_have: PhD, extra certifications, Spanish etc

Job Description:
{jd_text[:JD_MAX_CHARS]}
"""

    response = call_ollama(prompt)
    result   = parse_json_response(response)

    if result and isinstance(result, dict):
        # Fill missing keys with defaults
        for key in default:
            if key not in result:
                result[key] = default[key]

        # Lowercase required skills for matching
        result["required_skills"] = [
            s.lower().strip()
            for s in result.get("required_skills", [])
            if s
        ]

        # Split compound preferred skills
        # e.g. "actuarial (reserving, pricing)"
        # → ["actuarial", "reserving", "pricing"]
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

        result["preferred_skills"] = list(set(expanded))

        # Lowercase languages
        result["required_languages"] = [
            s.lower().strip()
            for s in result.get("required_languages", [])
            if s
        ]

        return result

    return default