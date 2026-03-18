# src/prompts/jd_prompt.py

import json
from pathlib import Path

JD_SCHEMA_PATH = Path("schemas/jd_schema.json")

def _get_jd_schema(path: Path) -> str:
    """
    Helper function to read and return JSON schema text from a file.
    Args:
        path (Path): Path to the JSON schema file
    Returns:
        str: JSON schema as a formatted string
    """

    with open(path, "r") as f:
        jd_schema = json.load(f)

        jd_schema_text = json.dumps(jd_schema, indent=2)

    return jd_schema_text

def get_jd_prompt(jd_text: str) -> str:
    """
    Generate prompt for extracting structured requirements from job description.

    Args:
        jd_text (str): Job description text

    Returns:
        str: Final prompt
    """
    jd_schema_text = _get_jd_schema(JD_SCHEMA_PATH)

    jd_prompt = f"""
    Extract structured information from the JD.

    Return JSON matching this format exactly.

    Schema Example:
    {jd_schema_text}

    JD:
    {jd_text}   

    JSON:
    """
    return jd_prompt