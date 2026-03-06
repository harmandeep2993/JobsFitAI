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
    
    except ValueError:
        raise ValueError()                                       # allow validation error to pass through
    
    except Exception as e:
        raise RuntimeError(f"Error extracting text from PDF: {e}")
    
    # Check for scanned or empty PDF
    if len(text.strip())<100:
        raise ValueError("PDF appears to be scanned or empty. Please upload a text-based PDF file")
    
    return text.strip()


def parser_doc(file_path):
    """
    Extract text content from a DOCX file using python-docx.
    Extracts from both paragraphs and tables to capture
    all resume content including structured skill tables.
    
    Args:
        file_path (str): Path to the DOCX file
        
    Returns:
        str: Extracted and cleaned text content
        
    Raises:
        FileNotFoundError : If file does not exist
        ValueError        : If document is empty
        RuntimeError      : If extraction fails
    """
    try:
        doc = Document(file_path)

        lines = []

        # Paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)

        # Tables
        for table in doc.tables:
            for row in table.rows:
                cells = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    lines.append(" | ".join(cells))

        # Headers and Footers
        for section in doc.sections:

            for para in section.header.paragraphs:
                text = para.text.strip()
                if text:
                    lines.append(text)

            for para in section.footer.paragraphs:
                text = para.text.strip()
                if text:
                    lines.append(text)

        # Remove duplicates while preserving order
        seen = set()
        clean_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                clean_lines.append(line)

        text = "\n".join(clean_lines)

        if len(text.strip()) < 100:
            raise ValueError(
                "DOCX appears to be empty or contains insufficient content"
            )

        return text.strip()

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

    except ValueError as e:
        raise ValueError(str(e))

    except Exception as e:
        raise RuntimeError(f"Error extracting text from DOCX: {e}")

# In testing, the direct content parsing from docx file was not reliable.
# Implement the docx to pdf converiosn and used pdfplumber to parse the content.

def parser_docx(file_path):
    
    path = Path(file_path)

    # Convert DOC/DOCX → PDF
    if path.suffix.lower() in (".docx", ".doc"):
        pdf_path = path.with_suffix(".pdf")
        convert(str(path), str(pdf_path))
        return parse_pdf(pdf_path)

    # If already PDF
    if path.suffix.lower() == ".pdf":
        return parse_pdf(path)

    # TXT fallback
    if path.suffix.lower() == ".txt":
        return Path(path).read_text()

    raise ValueError("Unsupported file format")


