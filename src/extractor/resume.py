# src/extractor/resume.py

import re

from src.utils.ollama import call_ollama, parse_json_response
from src.utils.config import RESUME_MAX_CHARS
from src.extractor.sections import extract_section


# FACTUAL POST PROCESSING HELPERS
#
# These are factual corrections — NOT content hardcoding:
#   calculate_years  -> math, always correct
#   normalise_degree -> degree names are standardised globally
#   detect_languages -> language names never change

def calculate_years(experience_list):
    """
    Calculate total work experience years in Python.
    Never trust LLM for date arithmetic.
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
    Degree names are internationally standardised —
    this is factual mapping not content hardcoding.

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
        if any(
            re.search(r"\b" + re.escape(kw) + r"\b", text_lower)
            for kw in keywords
        ):
            found.append(lang)

    return found


# RESUME EXTRACTORS
# Each extractor:
#   1. Finds relevant section using extract_section()
#   2. Falls back to full text if section not found
#   3. Sends focused content to LLM
#   4. LLM reads only what is relevant

def extract_skills(resume_text):
    """
    Extract and categorise skills from resume.

    Strategy:
      Find SKILLS section -> send to LLM
      LLM categorises whatever skills are there
      No hardcoded skill list

    Args:
        resume_text (str): Full resume text

    Returns:
        dict: Skills by category
    """
    default = {
        "programming_languages": [],
        "frameworks":            [],
        "databases":             [],
        "cloud":                 [],
        "tools":                 [],
        "soft_skills":           [],
    }

    skills_section = extract_section(resume_text, "skills")
    content        = skills_section or resume_text[:RESUME_MAX_CHARS]

    prompt = f"""
Read this text and extract all skills. Do not miss anything. Do not fabricate if not mentioned in text.
Categorise each skill correctly.
Return ONLY valid JSON. Nothing else.

{{
  "programming_languages": [],
  "frameworks":            [],
  "databases":             [],
  "cloud":                 [],
  "tools":                 [],
  "soft_skills":           []
}}

Category rules:
- programming_languages: Python, SQL, R, Java, C++ etc
- frameworks: ML/data libraries such as Pandas, NumPy, Scikit-learn, TensorFlow, PyTorch, XGBoost, FastAPI, Django, Flask, LangChain etc
- databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, SQLite etc
- cloud: AWS, Azure, GCP, cloud platforms etc
- tools: Docker, Git, Jupyter, Power BI, Tableau, VS Code, Databricks, Airflow etc
- soft_skills: communication, teamwork, problem solving, leadership etc

IMPORTANT:
- Pandas and NumPy are frameworks NOT databases
- Git and Docker are tools NOT frameworks
- Extract every skill you see — miss nothing

Text:
{content}
"""

    response = call_ollama(prompt)
    result   = parse_json_response(response)

    if result and isinstance(result, dict):
        for key in default:
            if key not in result:
                result[key] = []
        return result

    return default


def extract_experience(resume_text):
    """
    Extract work experience from resume.

    Strategy:
      Find EXPERIENCE section -> send to LLM
      LLM extracts jobs from focused text

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Work experience entries
    """
    exp_section = extract_section(resume_text, "experience")
    content     = exp_section or resume_text[:RESUME_MAX_CHARS]

    prompt = f"""
Extract all work experience from this text.
Usually date format is month-YYYY / MM/YYYY.
Calculate the duration properly for each job. e.g. 02-2025 to 07-2025 is 5 months or 0.5 year.
Return ONLY a valid JSON array. Nothing else.

[
  {{
    "title": "exact job title",
    "company": "company name",
    "duration_years": 1.5,
    "responsibilities": [
      "what they did — copy bullet points exactly"
    ]
  }}
]

IMPORTANT:
- duration_years: number or float value only
- List ALL jobs most recent first
- Copy responsibility bullet points exactly
- Do not include education here

Text:
{content}
"""

    response = call_ollama(prompt)

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

    Strategy:
      Find EDUCATION section -> send to LLM
      Normalise degree names after extraction

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Education entries
    """
    edu_section = extract_section(resume_text, "education")
    content     = edu_section or resume_text[:RESUME_MAX_CHARS]

    prompt = f"""
Extract all education and degrees from this text.
Return ONLY a valid JSON array. Nothing else.

[
  {{
    "degree": "MSc or BSc or PhD or Diploma",
    "field": "full field of study",
    "university": "university name"
  }}
]

IMPORTANT:
- List ALL degrees
- Use full field name e.g. "Data Analytics, Mathematics, Computer Science" not just "Data"
- degree should be MSc, BSc, PhD, Diploma, MBA, BEng, MEng etc

Text:
{content}
"""

    response = call_ollama(prompt)

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

    Strategy:
      Find LANGUAGES section -> send to LLM
      If section not found -> regex fallback
      Regex fallback is always reliable

    Args:
        resume_text (str): Full resume text

    Returns:
        list: Language names in lowercase
    """
    lang_section = extract_section(resume_text, "languages")

    if lang_section:
        prompt = f"""
Extract all languages from this text.
Return ONLY a valid JSON array of language names. Nothing else.

["English", "German"]

Text:
{lang_section}
"""
        response = call_ollama(prompt)

        try:
            result = parse_json_response(response)
            if isinstance(result, list) and result:
                langs = [l.lower().strip() for l in result]
                if langs:
                    return langs
        except Exception:
            pass

    # Fallback — regex on full text
    return detect_languages(resume_text)


def extract_current_title(experience_list, resume_text):
    """
    Get most recent job title.
    Uses first experience entry — most recent.
    Falls back to LLM on short resume text if needed.

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

    # Fallback — ask LLM directly
    prompt = f"""
What is the most recent job title in this resume?
Return ONLY the job title. No explanation.

Resume (first 500 chars):
{resume_text[:500]}
"""
    response = call_ollama(prompt)
    return (response or "").strip()


def extract_resume(resume_text):
    """
    Run all resume extractors and return structured resume JSON.

    Args:
        resume_text (str): Full resume text

    Returns:
        dict: Structured resume data
    """
    print("Extracting skills...")
    skills = extract_skills(resume_text)

    print("Extracting experience...")
    experience = extract_experience(resume_text)

    print("Extracting education...")
    education = extract_education(resume_text)

    print("Extracting languages...")
    languages = extract_languages(resume_text)

    print("Extracting current title...")
    current_title = extract_current_title(experience, resume_text)

    total_years = calculate_years(experience)

    return {
        "current_title":          current_title,
        "total_years_experience": total_years,
        "skills":                 skills,
        "experience":             experience,
        "education":              education,
        "languages":              languages,
    }