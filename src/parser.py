import os
import pdfplumber
from docx import Document
from pathlib import Path
from docx2pdf import convert


def parse_pdf(file_path):
    """
    Extract text content from a PDF file using pdfplumber.
    Handles multi-page PDFs and warns on empty pages.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted and cleaned text content
        
    Raises:
        FileNotFoundError : If file does not exist
        ValueError        : If PDF is scanned or empty
        RuntimeError      : If extraction fails
    """

    text = ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    print(f"Warning: page {i+1} returned no text")

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    
    except Exception as e:
        raise RuntimeError(f"Error extracting text from PDF: {e}")
    
    # Check for scanned or empty PDF
    if len(text.strip())<100:
        raise ValueError("PDF appears to be scanned or empty. Please upload a text-based PDF file")
    
    return text.strip()

# Direct text parsing from DOCX files was found to be unreliable during testing.
# To improve consistency, DOCX files are first converted to PDF format.
# The PDF is then parsed using pdfplumber to extract the text content.
# This approach provides more reliable and stable text extraction.

def parser_docx(file_path):
    
    path = Path(file_path)

    # Convert DOC/DOCX to PDF
    if path.suffix.lower() in (".docx", ".doc"):
        pdf_path = path.with_suffix(".pdf")
        try: 
            convert(str(path), str(pdf_path))
            return parse_pdf(str(pdf_path))

        finally:     
            if pdf_path.exists():
                pdf_path.unlink()

def extract_resume_text(file_path):
    """
    Detect file type and extract text from resume.
    Supported formats: PDF, DOCX, TXT
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf(path)

    elif suffix in [".docx", ".doc"]:
        return parser_docx(path)

    elif suffix == ".txt":
        return path.read_text(encoding="utf-8")

    else:
        raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT are supported.")