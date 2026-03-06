from src.parser import parse_pdf, parser_doc, parser_docx


def main():

    file_path = r"data\resume\sample_resume.docx"

    # choose parser based on file type
    if file_path.endswith(".pdf"):
        resume_text = parse_pdf(file_path)

    elif file_path.endswith(".doc"):
        resume_text = parser_doc(file_path)

    elif file_path.endswith(".docx"):
        resume_text = parser_docx(file_path)

    else:
        raise ValueError("Unsupported file format")

    print(resume_text)


if __name__ == "__main__":
    main()