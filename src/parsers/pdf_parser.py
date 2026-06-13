# src/parsers/pdf_parser.py

"""
PDF text extraction with three-tier fallback strategy:

    Tier 1 - pdfplumber  : best for structured/text-based PDFs
    Tier 2 - PyMuPDF     : fallback for complex layouts pdfplumber struggles with
    Tier 3 - OCR         : last resort for scanned/image-based PDFs

Each tier is tried in order. If a tier returns enough text it is used.
OCR requires optional dependencies: pytesseract + pdf2image + poppler.
"""

from pathlib import Path

from src.utils.config import MIN_TEXT_LIMIT
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Tier 1: pdfplumber


def _extract_pdfplumber(file_path: str) -> str:
    """
    Extract text using pdfplumber.
    Best for standard text-based PDFs with clean layouts.

    Args:
        file_path (str): Path to PDF file

    Returns:
        str: Extracted text or empty string if failed
    """
    try:
        import pdfplumber

        pages = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages.append(page_text.strip())
                else:
                    logger.warning("pdfplumber: page %d returned no text", i + 1)

        return "\n\n".join(pages).strip()

    except ImportError:
        logger.warning("pdfplumber not installed - skipping tier 1")
        return ""
    except Exception as e:
        logger.error("pdfplumber failed: %s", e)
        return ""


# Tier 2: PyMuPDF


def _extract_pymupdf(file_path: str) -> str:
    """
    Extract text using PyMuPDF (fitz).
    Better than pdfplumber for complex layouts, multi-column, and rotated text.

    Args:
        file_path (str): Path to PDF file

    Returns:
        str: Extracted text or empty string if failed
    """
    try:
        import fitz  # PyMuPDF

        pages = []
        doc = fitz.open(file_path)

        for i, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                pages.append(page_text.strip())
            else:
                logger.warning("PyMuPDF: page %d returned no text", i + 1)

        doc.close()
        return "\n\n".join(pages).strip()

    except ImportError:
        logger.warning("PyMuPDF (fitz) not installed - skipping tier 2")
        return ""
    except Exception as e:
        logger.error("PyMuPDF failed: %s", e)
        return ""


# Tier 3: OCR


def _extract_ocr(file_path: str) -> str:
    """
    Extract text using OCR (pytesseract + pdf2image).
    Last resort for scanned or image-based PDFs.
    Requires: pytesseract, pdf2image, and poppler installed on system.

    Args:
        file_path (str): Path to PDF file

    Returns:
        str: OCR extracted text or empty string if failed
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path

        logger.info("Attempting OCR extraction - this may take a moment...")

        images = convert_from_path(file_path, dpi=300)
        pages = []

        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang="eng")
            if page_text and page_text.strip():
                pages.append(page_text.strip())
            else:
                logger.warning("OCR: page %d returned no text", i + 1)

        return "\n\n".join(pages).strip()

    except ImportError:
        logger.warning(
            "OCR dependencies not installed (pytesseract/pdf2image) - skipping tier 3"
        )
        return ""
    except Exception as e:
        logger.error("OCR failed: %s", e)
        return ""


# Quality check


def _is_good_extraction(text: str) -> bool:
    """
    Check if extracted text meets minimum quality threshold.
    Rejects text that is too short or mostly garbled/non-printable characters.

    Args:
        text (str): Extracted text

    Returns:
        bool: True if text is usable
    """
    if not text or len(text.strip()) < MIN_TEXT_LIMIT:
        return False

    printable = sum(1 for c in text if c.isprintable())
    ratio = printable / len(text)

    if ratio < 0.70:
        logger.warning("Text quality poor - printable ratio: %.2f", ratio)
        return False

    return True


# Public API


def parse_pdf(file_path: str) -> str:
    """
    Extract text from a PDF using three-tier fallback strategy.

        Tier 1 - pdfplumber  (fastest, best for standard PDFs)
        Tier 2 - PyMuPDF     (better for complex layouts)
        Tier 3 - OCR         (scanned/image PDFs, slowest)

    Args:
        file_path (str): Path to PDF file

    Returns:
        str: Extracted text content

    Raises:
        FileNotFoundError : File does not exist
        ValueError        : PDF is unreadable - all tiers failed
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {path.suffix}")

    logger.info("Parsing PDF: %s", path.name)

    # Tier 1
    logger.debug("Trying tier 1: pdfplumber")
    text = _extract_pdfplumber(file_path)

    if _is_good_extraction(text):
        logger.info("Tier 1 succeeded - %d chars extracted", len(text))
        return text

    # Tier 2
    logger.warning("Tier 1 insufficient - trying tier 2: PyMuPDF")
    text = _extract_pymupdf(file_path)

    if _is_good_extraction(text):
        logger.info("Tier 2 succeeded - %d chars extracted", len(text))
        return text

    # Tier 3
    logger.warning("Tier 2 insufficient - trying tier 3: OCR")
    text = _extract_ocr(file_path)

    if _is_good_extraction(text):
        logger.info("Tier 3 (OCR) succeeded - %d chars extracted", len(text))
        return text

    # All tiers failed
    logger.error("All extraction tiers failed for: %s", path.name)
    raise ValueError(
        "Could not extract readable text from this PDF. "
        "The file may be corrupted, password-protected, or a scanned image "
        "without OCR support installed."
    )
