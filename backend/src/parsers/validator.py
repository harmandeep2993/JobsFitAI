# src/parsers/validator.py

"""
File validation for uploaded resume files.

Validates before any parsing attempt:
    - File existence
    - File size limit
    - Supported file format
    - MIME type matches extension
    - File is not corrupted (basic header check)
"""

from pathlib import Path

from src.utils.config import MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Validation constants
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


ALLOWED_MIME_TYPES = {
    ".pdf": ["application/pdf"],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",  # DOCX files are ZIP archives
    ],
    ".txt": ["text/plain"],
}

# Magic bytes (file headers) for format verification
FILE_SIGNATURES = {
    ".pdf": b"%PDF",
    ".docx": b"PK\x03\x04",  # ZIP header - DOCX is a ZIP archive
    # ".doc":  b"\xd0\xcf\x11\xe0",  # Microsoft Compound Document
}


# Individual validators


def _check_exists(path: Path) -> None:
    """
    Check file exists at the given path.

    Args:
        path (Path): File path

    Raises:
        FileNotFoundError: If file does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")


def _check_size(path: Path) -> None:
    """
    Check file size does not exceed the maximum allowed size.

    Args:
        path (Path): File path

    Raises:
        ValueError: If file exceeds size limit or is empty
    """
    size = path.stat().st_size

    if size == 0:
        raise ValueError(f"File is empty: {path.name}")

    if size > MAX_FILE_SIZE_BYTES:
        size_mb = size / (1024 * 1024)
        raise ValueError(
            f"File too large: {size_mb:.1f} MB. "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    logger.info("File size: %.2f MB", size / (1024 * 1024))


def _check_extension(path: Path) -> None:
    """
    Check file extension is supported.

    Args:
        path (Path): File path

    Raises:
        ValueError: If extension is not supported
    """
    ext = path.suffix.lower()

    # check .doc extension after the supported check
    # because .doc is not supported by python-docx and we want to allow it with a warning
    if ext == ".doc":
        logger.warning(
            ".doc format has limited support - convert to .docx for best results."
        )

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    logger.info("File extension: %s", ext)


def _check_mime_type(path: Path) -> None:
    """
    Check MIME type matches the file extension.
    Prevents misnamed files (e.g. a .exe renamed to .pdf).

    Args:
        path (Path): File path

    Raises:
        ValueError: If MIME type does not match extension
    """
    try:
        import magic

        mime = magic.from_file(str(path), mime=True)
        ext = path.suffix.lower()

        allowed = ALLOWED_MIME_TYPES.get(ext, [])

        if mime not in allowed:
            logger.warning(
                "MIME type mismatch - extension: %s, detected: %s", ext, mime
            )
            raise ValueError(
                f"File content does not match extension. "
                f"Expected {ext} file but detected: {mime}"
            )

        logger.info("MIME type verified: %s", mime)

    except ValueError:
        raise
    except ImportError:
        logger.debug("python-magic not installed - skipping MIME type check")
    except Exception as e:
        logger.warning("MIME check failed unexpectedly: %s - skipping", e)


def _check_signature(path: Path) -> None:
    """
    Check file magic bytes match expected format signature.
    Provides a fast corruption check without fully parsing the file.
    TXT files are skipped as they have no fixed signature.

    Args:
        path (Path): File path

    Raises:
        ValueError: If file signature does not match expected format
    """
    ext = path.suffix.lower()

    if ext == ".txt":
        return

    expected_sig = FILE_SIGNATURES.get(ext)
    if not expected_sig:
        return

    try:
        with open(path, "rb") as f:
            header = f.read(len(expected_sig))

        if header != expected_sig:
            raise ValueError(
                f"File appears corrupted or is not a valid {ext} file. "
                "Please upload the file again."
            )

        logger.info("File signature verified for: %s", path.name)

    except ValueError:
        raise
    except Exception as e:
        logger.warning("Could not verify file signature: %s", e)


# Public API


def validate(file_path: str) -> None:
    """
    Run all validation checks on an uploaded resume file.

    Checks performed in order:
        1. File exists
        2. File size within limit
        3. Extension is supported
        4. MIME type matches extension
        5. File signature (magic bytes) is valid

    Args:
        file_path (str): Path to the uploaded file

    Returns:
        None - raises on any validation failure

    Raises:
        FileNotFoundError : File does not exist
        ValueError : Any validation check failed
    """
    path = Path(file_path)

    logger.info("Validating file: %s", path.name)

    _check_exists(path)
    _check_size(path)
    _check_extension(path)
    _check_mime_type(path)
    _check_signature(path)

    logger.info("Validation passed: %s", path.name)
