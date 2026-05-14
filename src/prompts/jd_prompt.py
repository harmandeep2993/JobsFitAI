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

# Module-level constant — schema path
JD_SCHEMA_PATH = Path("schemas/jd_schema.json")


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
    """
    Build extraction prompt for a job description.

    Args:
        jd_text (str): Raw job description text

    Returns:
        str: Final prompt string ready for LLM
    """
    schema_text = _get_jd_schema()

    prompt = f"""Extract structured information from the job description below.
Return JSON matching the schema exactly.
Do not infer or add information not explicitly stated.
If a field is missing use empty string, empty list, or 0 as appropriate.

Schema:
{schema_text}

Job Description:
{jd_text}

JSON:"""

    logger.info("JD length: %d characters", len(jd_text))
    logger.info("JD prompt length: %d characters", len(prompt))
    logger.info("JD prompt ready")

    return prompt