# src/prompts/jd_prompt.py

import json
from pathlib import Path
from src.utils.logger import get_logger
    
logger = get_logger(__name__)

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
    
    jd_schema_length = len(jd_schema_text)

    logger.info("Loaded JD schema from %s", path)
    logger.info("JD schema length: %d characters", jd_schema_length)
    
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
    Important: Do not infer or add any information that is not explicitly stated in the JD.

    Extract structured information from the JD. Return JSON matching this format exactly. 
    Do not deviate from the schema. If information is missing, use empty strings, empty lists, or 0 as appropriate.

    Schema Example:
    {jd_schema_text}

    JD:
    {jd_text}   

    JSON:
    """

    jd_text_length = len(jd_text)
    jd_prompt_length = len(jd_prompt)

    logger.info("JD text length: %d characters", jd_text_length)
    logger.info("Generated JD prompt length: %d characters", jd_prompt_length)
    logger.info("JD prompt Ready with schema and JD text!")

    return jd_prompt