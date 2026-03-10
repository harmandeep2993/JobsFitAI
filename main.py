# main.py

from pathlib import Path
from src.parser.parser import extract_resume_text


def main():
    file_path = Path(r"data\pdf_resume\harmandeep_singh_resume.pdf")
    resume_text = extract_resume_text(file_path)
    print(resume_text)


if __name__ == "__main__":
    main()