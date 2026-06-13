# src/parsers/text_cleaner.py

"""
Text cleaning utilities for extracted resume and job description text.

Handles common issues found in PDF and DOCX extracted text:
    - Excessive whitespace and blank lines
    - Broken words from PDF line wrapping (e.g. experi-\nence)
    - Unicode normalization (smart quotes, special dashes, accents)
    - Non-printable and control characters
    - Repeated punctuation artifacts
"""

import re
import unicodedata

from src.utils.logger import get_logger

logger = get_logger(__name__)


# Unicode normalization


def _normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters to ASCII-compatible equivalents.
    Handles smart quotes, special dashes, ligatures, and accented characters.

    Args:
        text (str): Raw extracted text

    Returns:
        str: Unicode normalized text
    """
    # Normalize to NFC form first (composed characters)
    text = unicodedata.normalize("NFC", text)

    # Replace smart quotes with standard quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")  # single smart quotes
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # double smart quotes

    # Replace special dashes with standard hyphen
    text = text.replace("\u2013", "-").replace("\u2014", "-")  # en-dash, em-dash

    # Replace bullet point variants with a standard dash
    text = text.replace("\u2022", "-").replace(
        "\u2023", "-"
    )  # bullet, triangular bullet
    text = text.replace("\u25cf", "-").replace("\u25cb", "-")  # filled/empty circle

    # Replace non-breaking space with regular space
    text = text.replace("\u00a0", " ")

    return text


# Broken word repair


def _fix_broken_words(text: str) -> str:
    """
    Fix hyphenated line breaks introduced by PDF extraction.
    Example: experi-\nence → experience

    Only joins when a word ends with a hyphen followed by a newline
    and continues with a lowercase letter (avoids joining intentional hyphens).

    Args:
        text (str): Text with possible broken words

    Returns:
        str: Text with broken words rejoined
    """
    # Pattern: word-\nnextword → wordnextword
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return text


# Whitespace cleanup


def _clean_whitespace(text: str) -> str:
    """
    Remove excessive whitespace, normalize line endings,
    and collapse multiple blank lines into a single blank line.

    Args:
        text (str): Text with irregular whitespace

    Returns:
        str: Cleaned text with normalized whitespace
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse more than 2 consecutive blank lines into 1
    cleaned = []
    blank_count = 0

    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    return "\n".join(cleaned).strip()


# Non-printable character removal


def _remove_non_printable(text: str) -> str:
    """
    Remove non-printable and control characters from text.
    Keeps standard whitespace characters (space, newline, tab).

    Args:
        text (str): Text possibly containing control characters

    Returns:
        str: Text with non-printable characters removed
    """
    # Keep printable chars plus newline and tab
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in ("\n", "\t"))
    return cleaned


# Repeated punctuation cleanup


def _clean_punctuation(text: str) -> str:
    """
    Clean up repeated punctuation artifacts from PDF extraction.
    Example: "Python........." → "Python"
             "---Skills---"   → "Skills"

    Args:
        text (str): Text with punctuation artifacts

    Returns:
        str: Text with cleaned punctuation
    """
    # Remove lines that are only punctuation/symbols (separator lines)
    text = re.sub(r"^\s*[=\-_*#|~]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Replace multiple dots with single space
    text = re.sub(r"\.{3,}", " ", text)

    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text


# Public API


def clean(text: str) -> str:
    """
    Apply full cleaning pipeline to extracted text.

    Pipeline order:
        1. Remove non-printable characters
        2. Normalize unicode
        3. Fix broken words from PDF line wrapping
        4. Clean punctuation artifacts
        5. Normalize whitespace

    Args:
        text (str): Raw extracted text from PDF or DOCX

    Returns:
        str: Cleaned text ready for LLM extraction

    Raises:
        ValueError: If input text is empty or None
    """
    if not text or not text.strip():
        raise ValueError("Cannot clean empty text")

    original_len = len(text)

    text = _remove_non_printable(text)
    text = _normalize_unicode(text)
    text = _fix_broken_words(text)
    text = _clean_punctuation(text)
    text = _clean_whitespace(text)

    logger.info(
        "Text cleaning complete - %d chars → %d chars (%.1f%% reduction)",
        original_len,
        len(text),
        (1 - len(text) / original_len) * 100 if original_len > 0 else 0,
    )

    return text
