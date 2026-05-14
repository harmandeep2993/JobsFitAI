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

# Module-level constant — schema path
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
    """
    Build extraction prompt for a resume.

    Args:
        resume_text (str): Raw resume text

    Returns:
        str: Final prompt string ready for LLM
    """
    schema_text = _get_resume_schema()

    prompt = f"""Extract structured information from the resume below.
Return JSON matching the schema exactly.
Do not infer missing information.
Extract ALL skill keywords explicitly mentioned regardless of which section they appear in.
If a section is missing return empty list or null for that field.
Calculate total experience from the experience section only. If missing use 0.

Schema:
{schema_text}

Resume:
{resume_text}

JSON:"""

    logger.info("Resume length: %d characters", len(resume_text))
    logger.info("Resume prompt length: %d characters", len(prompt))
    logger.info("Resume prompt ready")

    return prompt