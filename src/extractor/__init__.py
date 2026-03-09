# src/extractor/__init__.py

from utils.ollama_utils import check_ollama
from src.extractor.resume import extract_resume
from src.extractor.jd import extract_jd


def extract_all(resume_text, jd_text):
    """
    Extract structured data from resume and JD.

    Args:
        resume_text (str): Raw resume text
        jd_text     (str): Raw job description text

    Returns:
        tuple: (resume_json, jd_json)
               Empty dicts if Ollama not running
    """
    if not check_ollama():
        print("Error: Ollama is not running")
        print("Start with: ollama serve")
        return {}, {}

    print("Extracting resume...")
    resume_json = extract_resume(resume_text)

    print("Extracting job description...")
    jd_json = extract_jd(jd_text)

    return resume_json, jd_json