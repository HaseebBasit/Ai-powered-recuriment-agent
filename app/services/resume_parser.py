import os
from pathlib import Path

def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF (fitz)"""
    import fitz  # PyMuPDF
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"Error extracting text from PDF ({file_path}): {e}")
    return text.strip()

def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx"""
    import docx
    text = []
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text:
                text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        text.append(cell.text)
    except Exception as e:
        print(f"Error extracting text from DOCX ({file_path}): {e}")
    return "\n".join(text).strip()

def extract_resume_text(file_path):
    """Extract text based on file extension (.pdf or .docx)"""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        # Fallback raw read
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return ""

