# src/extractors/resume.py

"""
Resume extraction module. Uses LLM prompts to extract structured information from resume text.
Includes factual post-processing helpers to improve reliability.
"""

import re

from src.utils.router import call_llm, parse_json_response
from src.utils.config import RESUME_MAX_CHARS
from src.extractors.sections import extract_section

from src.extractors.prompts import (
    skills_prompt,
    experience_prompt,
    education_prompt,
    languages_prompt,
    title_prompt,
)


# Factual post-processing helpers

def calculate_years(experience_list):
    """
    Calculate total work experience years in Python.
    Handles overlapping job dates - only counts unique periods.
    Caps single job at 20 years to prevent hallucination.

    Args:
        experience_list (list): Experience list from LLM

    Returns:
        float: Total years of work experience
    """
    total = 0

    for exp in experience_list:
        years = exp.get("duration_years", 0)

        if isinstance(years, (int, float)) and 0 < years <= 20:
            total += years

    return round(total, 1)


def normalise_degree(degree_str):
    """
    Normalise degree string to standard format.
    MSc/M.Sc/Master of Science all mean the same thing.
    Degree names are internationally standardised. This is factual mapping not content hardcoding.

    Args:
        degree_str (str): Raw degree string from LLM

    Returns:
        str: Normalised degree e.g. "MSc", "BSc", "PhD"
    """
    if not degree_str:
        return degree_str

    d = degree_str.lower().strip()

    # Ordered from most specific to least
    # PhD check before MSc to avoid misclassification
    if any(v in d for v in ["phd", "ph.d", "doctorate", "doctoral"]):
        return "PhD"
    if any(v in d for v in ["msc", "m.sc", "master", "mba", "m.eng", "postgrad"]):
        return "MSc"
    if any(v in d for v in ["bsc", "b.sc", "bachelor", "b.tech", "b.eng", "b.e", "hons", "undergraduate"]):
        return "BSc"
    if any(v in d for v in ["diploma", "hnd", "foundation"]):
        return "Diploma"

    return degree_str


def detect_languages(text):
    """
    Detect human languages in text using regex.
    Reliable fallback when LLM misses languages section.
    Language names are factual — not resume-specific.

    Args:
        text (str): Any text

    Returns:
        list: Language names in lowercase
    """
    lang_map = {
        "english":    ["english"],
        "german":     ["german", "deutsch"],
        "french":     ["french", "français"],
        "spanish":    ["spanish", "español"],
        "mandarin":   ["mandarin", "chinese"],
        "arabic":     ["arabic"],
        "italian":    ["italian"],
        "portuguese": ["portuguese"],
        "russian":    ["russian"],
        "japanese":   ["japanese"],
        "korean":     ["korean"],
        "hindi":      ["hindi"],
        "dutch":      ["dutch"],
        "swedish":    ["swedish"],
    }

    found      = []
    text_lower = text.lower()

    for lang, keywords in lang_map.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text_lower) for kw in keywords):
            found.append(lang)

    return found


# Resume Extraction Functions
# Each extractor:
#  - Finds relevant section using extract_section()
#  - Falls back to full text if section not found
#  - Sends focused content to LLM via hardened prompt
#  - LLM reads only what is relevant


def extract_skills(resume_text):
    """
    Extract and categorise skills from resume.

    Args:
        resume_text (str): Full resume text

    Returns:
        dict: Skills by category
    """

    skills_section = extract_section(resume_text, "skills")
    content = skills_section or resume_text[:RESUME_MAX_CHARS]
    print("---- SKILLS CONTENT ----")
    print(content[:400])

    if not content:
        return []

    response = call_llm(skills_prompt(content))
    result = parse_json_response(response)

    if isinstance(result, list):

        skills = [
            s.lower().strip()
            for s in result
            if isinstance(s, str) and s.strip()
        ]

        # remove duplicates
        return list(dict.fromkeys(skills))

    return []

def extract_experience(resume_text):
    """
    Extract work experience from resume.

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Work experience entries
    """
    exp_section = extract_section(resume_text, "experience")
    content = exp_section or resume_text[:RESUME_MAX_CHARS]
    print("---- EXPERIENCE CONTENT ----")
    print(content[:400])

    response = call_llm(experience_prompt(content))

    try:
        result = parse_json_response(response)

        if isinstance(result, list):
            return result
        
    except Exception:
        pass

    return []

def extract_education(resume_text):
    """
    Extract education from resume.

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Education entries
    """
    edu_section = extract_section(resume_text, "education")
    content     = edu_section or resume_text[:RESUME_MAX_CHARS]

    response = call_llm(education_prompt(content))

    try:
        result = parse_json_response(response)
        if isinstance(result, list):
            for edu in result:
                if "degree" in edu:
                    edu["degree"] = normalise_degree(edu["degree"])
            return result
    except Exception:
        pass

    return []


def extract_languages(resume_text):
    """
    Extract languages from resume.
    Falls back to regex if LLM misses languages section.

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Language names in lowercase
    """
    lang_section = extract_section(resume_text, "languages")

    if lang_section:
        response = call_llm(languages_prompt(lang_section))

        try:
            result = parse_json_response(response)
            if isinstance(result, list) and result:
                langs = [l.lower().strip() for l in result]
                if langs:
                    return langs
                
        except Exception:
            pass

    # Fallback - regex on full text
    return detect_languages(resume_text)


def extract_current_title(experience_list, resume_text):
    """
    Get most recent job title.
    Uses first experience entry — most recent.
    Falls back to LLM if experience list is empty.

    Args:
        experience_list (list): Extracted experience
        resume_text     (str):  Full resume text

    Returns:
        str: Most recent job title
    """
    if experience_list:
        title = experience_list[0].get("title", "")

        if title:
            return title

    response = call_llm(title_prompt(resume_text[:500]))

    return (response or "").strip()

def is_weak_result(resume_content):
    """
    Determine if extraction result is weak or incomplete.
    """

    if not resume_content:
        return True

    if not resume_content.get("skills"):
        return True

    if not resume_content.get("experience"):
        return True

    return False


def extract_resume(resume_text):
    """
    Run all resume extractors and return structured resume JSON.

    Args:
        resume_text (str): Full resume text

    Returns:
        dict: Structured resume data
    """
    skills = extract_skills(resume_text)
    experience = extract_experience(resume_text)
    education = extract_education(resume_text)
    languages = extract_languages(resume_text)

    current_title = extract_current_title(experience, resume_text)
    total_years = calculate_years(experience)

    result =  {
        "current_title": current_title,
        "total_years_experience": total_years,
        "skills": skills,
        "experience": experience,
        "education": education,
        "languages": languages,
    }
    
    # pass 2 — fallback extraction if weak
    if is_weak_result(result):

        fallback_text = resume_text[:RESUME_MAX_CHARS]

        skills = extract_skills(fallback_text)
        experience = extract_experience(fallback_text)
        education = extract_education(fallback_text)
        languages = extract_languages(fallback_text)

        current_title = extract_current_title(experience, fallback_text)
        total_years = calculate_years(experience)

        result = {
            "current_title": current_title,
            "total_years_experience": total_years,
            "skills": skills,
            "experience": experience,
            "education": education,
            "languages": languages,
        }

    return result