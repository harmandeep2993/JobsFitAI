# src/prompts/resume_prompt.py
"""
Prompt builder for resume extraction.

Loads the resume schema and builds a structured extraction prompt
for the LLM to return a JSON object matching the schema.
"""

import json
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

RESUME_SCHEMA_PATH = (
    Path(__file__).parent.parent.parent / "schemas" / "resume_schema.json"
)


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
    2. Resume may be in any language - extract and return ALL values in English.
    3. skills: extract ALL skill keywords and technologies into the skills[] list - scan every section without exception: experience bullet points, project technologies and descriptions, certifications, summary, skills section, publications. Include programming languages, frameworks, libraries, tools, platforms, cloud services, databases, methodologies, domain knowledge, and soft skills. Every technology or tool mentioned anywhere in the resume must appear in skills[].
    4. experience_entries: extract ALL roles - full-time, part-time, freelance, internship, trainee, research, academic. For functional resumes with no dates extract roles from any experience section.
    5. start_date, end_date: extract the start AND end date for EVERY role that shows any dates. Dates may appear in different forms - "MM/YYYY", "Month YYYY" (e.g. Dec 2025), "YYYY", or a range like "Oct 2021 - May 2023" or "2021-2023". Normalize each to "MM/YYYY" when a month is known, otherwise "YYYY". For ongoing/current roles (Present, Current, till date, heute) set end_date to "present". Only use "" when the role shows no date at all. Never invent dates, but always capture the dates that ARE shown - do not leave older roles blank if they have dates. Do NOT calculate durations.
    6. duration_years and meta.total_experience_years: always set these to 0. They are calculated automatically after extraction - never compute them yourself.
    7. projects: extract ALL projects, research, publications, campaigns, or independent work. title and description are mandatory - never leave empty if text exists. technologies[]: extract from title and description text.
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
