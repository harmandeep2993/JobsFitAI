# src/prompts/jd_prompt.py
"""
Prompt builder for job description extraction.

Loads the JD schema and builds a structured extraction prompt
for the LLM to return a JSON object matching the schema.
"""

import json
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Absolute path so it resolves correctly regardless of working directory
JD_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "jd_schema.json"


def _get_jd_schema() -> str:
    """
    Load and return the JD schema as a formatted JSON string.

    Returns:
        str: JD schema as indented JSON string

    Raises:
        FileNotFoundError: If schema file does not exist
    """
    with open(JD_SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    schema_text = json.dumps(schema, indent=2)

    logger.info("Loaded JD schema from %s", JD_SCHEMA_PATH)
    logger.info("JD schema length: %d characters", len(schema_text))

    return schema_text


def get_jd_prompt(jd_text: str) -> str:
    """Build the LLM extraction prompt for a raw job description string."""
    schema_text = _get_jd_schema()

    prompt = f"""Extract job description data into this JSON schema. Follow all rules strictly.

    RULES:
    1. Return ONLY valid JSON. No markdown, no explanation, no extra text.
    2. JD may be in any language - extract and return ALL values in English.
    3. required_skills: ALL skills, tools, technologies, competencies marked as required or essential. Split compound entries into individual items (e.g. "Python incl. Pydantic-AI, LangGraph" → ["python", "pydantic-ai", "langgraph"]).
    4. preferred_skills: bonus, nice-to-have, or optional skills only.
    5. responsibilities: split into individual action items. Translate to English.
    6. experience_requirements: explicit statements only. Empty list if none stated.
    7. education_requirements: explicit statements only. Empty list if none stated.
    8. work_mode: remote|hybrid|on-site|not specified
    9. employment_type: full-time|part-time|contract|internship|not specified
    10. job_level: junior|mid-level|senior|lead|not specified
    11. job_summary: 1-2 sentences describing the ROLE and KEY RESPONSIBILITIES only. Not the company intro. Write in English.
    12. Missing fields → empty string, empty list, or 0.

    SCHEMA:
    {schema_text}

    JOB DESCRIPTION:
    {jd_text}

    JSON:"""

    logger.info("JD length: %d characters", len(jd_text))
    logger.info("JD prompt length: %d characters", len(prompt))
    logger.info("JD prompt ready")

    return prompt
