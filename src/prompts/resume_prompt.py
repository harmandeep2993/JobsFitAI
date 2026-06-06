# src/prompts/resume_prompt.py
"""
Prompt builder for resume extraction.

Loads the resume schema and builds a structured extraction prompt
for the LLM to return a JSON object matching the schema.
"""

import json
import datetime as dt
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

RESUME_SCHEMA_PATH = Path("schemas/resume_schema.json")


def _get_resume_schema() -> str:
    """
    Load and return the resume schema as a formatted JSON string.

    Returns:
        str: Resume schema as indented JSON string

    Raises:
        FileNotFoundError: If schema file does not exist
    """
    with open(RESUME_SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    schema_text = json.dumps(schema, indent=2)

    logger.info("Loaded resume schema from %s", RESUME_SCHEMA_PATH)
    logger.info("Resume schema length: %d characters", len(schema_text))

    return schema_text


def get_resume_prompt(resume_text: str) -> str:
    """Build the prompt for resume extraction.  
    Args:
        resume_text (str): The raw text of the resume to be extracted.
    Returns:
        str: The complete prompt to be sent to the LLM for extraction.
    """
    schema_text = _get_resume_schema()

    prompt = f"""Extract resume data into this JSON schema. Follow all rules strictly.

    RULES:
    1. Return ONLY valid JSON. No markdown, no explanation, no extra text.
    2. Resume may be in any language — extract and return ALL values in English.
    3. skills: extract ALL skills keywords from every section (experience, projects, certifications, summary, skills, publications). Include technical skills, tools, frameworks, soft skills, methodologies, domain knowledge.
    4. experience_entries: extract ALL roles — full-time, part-time, freelance, internship, trainee, research, academic. For functional resumes with no dates extract roles from any experience section.
    5. duration_years: calculate difference end_date - start_date and round to 1 decimal. If end_date is present/current/heute/actuellement or equivalent → use today's date ({dt.date.today()}). If only years given → assume Jan for start, Dec for end. Use 0.0 if dates missing.
    6. meta.total_experience_years: sum of ALL duration_years rounded to 1 decimal. Use 0.0 if no experience.
    7. projects: extract ALL projects, research, publications, campaigns, or independent work. title and description are mandatory — never leave empty if text exists. technologies[]: extract from title and description text.
    8. education: extract degree, field, institution. Translate degree names to English (e.g. Diplom → Diploma, Magister → Master, Licence → Bachelor).
    9. languages: extract as stated. certifications: extract if mentioned.
    10. candidate.name/title/location: extract from header or contact section.
    11. Missing fields → empty string, empty list, or 0.

    SCHEMA:
    {schema_text}

    RESUME:
    {resume_text}

    JSON:"""

    logger.info("Resume length: %d characters", len(resume_text))
    logger.info("Resume prompt length: %d characters", len(prompt))
    logger.info("Resume prompt ready")

    return prompt