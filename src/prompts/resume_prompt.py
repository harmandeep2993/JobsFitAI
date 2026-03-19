# src/prompts/resume_prompt.py

import json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_resume_schema(schema_type):
    """
    Helper function to read and return JSON schema text from a file.
    
    Args:
        schema_type (str): "Detailed" or "Summary" to determine which schema to use
        Returns: str: JSON schema as a formatted string 
    """
    schema_type= schema_type.lower().strip()

    if schema_type == "detailed":
        file_path = Path("schemas/resume_schema_detailed.json")

    elif schema_type ==  "quick":
        file_path = Path("schemas/resume_schema_small.json")

    else:
        raise ValueError("Invalid schema type. Use 'Detailed' or 'Quick'.")
    
    with open(file_path, "r") as f:
        schema_json = json.load(f)
    schema_text = json.dumps(schema_json, indent=4)

    schema_text_length = len(schema_text)
    
    logger.info(f"Loaded {schema_type} resume schema from {file_path}")
    logger.info(f"Resume schema text length: {schema_text_length} characters")
    
    return schema_text

# Resume Prompt Function
def get_resume_prompt(schema_type, resume_text):
    """
    Generate prompt for extracting structured resume information based on schema type.
    
    args:
        schema_type (str): "Detailed" or "Quick" to determine which schema to use
        resume_text (str): The text of the resume to be processed
    returns:
        str: Final prompt string
    """
    
    schema_text = _get_resume_schema(schema_type)


    resume_prompt = f"""

    Important: Do not infer or add any information that is not explicitly stated in the resume.

    Extract structured information from the resume.

    Return JSON matching this format exactly.

    Schema Example:
    {schema_text}

    Resume:
    {resume_text}

    JSON:
    """
    resume_prompt_length = len(resume_prompt)

    logger.info(f"Resume text length: {len(resume_text)} characters")
    logger.info(f"Total resume prompt length: {resume_prompt_length} characters")
    logger.info("Resume prompt ready with schema and resume text!")

    return resume_prompt