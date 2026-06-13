# src/parsers/resume_parser.py

"""
Resume parsing entry point for JobsFitAI.

Orchestrates the full parsing pipeline:
    1. Validate   — check file before attempting extraction
    2. Extract    — route to correct parser based on file type
    3. Clean      — normalize and clean extracted text

Supported formats: PDF, DOCX, DOC, TXT

Usage:
    from src.parsers.resume_parser import extract_all_text
    text = extract_all_text("resume.pdf")
"""

from pathlib import Path

from src.parsers.validator import validate
from src.parsers.pdf_parser import parse_pdf
from src.parsers.docx_parser import parse_docx
from src.parsers.text_cleaner import clean
from src.utils.logger import get_logger

# 
logger = get_logger(__name__)


def extract_all_text(file_path: str) -> str:
    """
    Full parsing pipeline — validate, extract, and clean resume text.

    Args:
        file_path (str): Path to the uploaded resume file

    Returns:
        str: Cleaned extracted text ready for LLM extraction

    Raises:
        FileNotFoundError : File does not exist
        ValueError        : Validation failed or unsupported format
        RuntimeError      : Extraction failed
    """
    path = Path(file_path)
    logger.debug("Starting parsing pipeline for: %s", path.name)

    # Step 1: Validate
    validate(file_path)

    # Step 2: Extract based on file type
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        raw_text = parse_pdf(file_path)

    elif suffix in (".docx", ".doc"):
        raw_text = parse_docx(file_path)

    elif suffix == ".txt":
        logger.debug("Reading TXT file: %s", path.name)
        raw_text = path.read_text(encoding="utf-8").strip()

    else:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            "Supported formats: PDF, DOCX, DOC, TXT"
        )

    # Step 3: Clean
    cleaned_text = clean(raw_text)

    logger.info("Resume parsed: %d chars from %s", len(cleaned_text), path.name)

    return cleaned_text