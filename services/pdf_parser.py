# services/pdf_parser.py

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Clean the uploaded filename so it is safe to save locally.
    """
    filename = Path(filename).name
    filename = re.sub(r"[^\w\-. ]", "_", filename)
    filename = filename.replace(" ", "_")
    return filename


def save_uploaded_pdf(uploaded_file) -> str:
    """
    Save a Streamlit uploaded PDF file to disk.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        str: path to saved PDF
    """
    safe_name = sanitize_filename(uploaded_file.name)
    save_path = UPLOAD_DIR / safe_name

    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())

    return str(save_path)


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted PDF text for better downstream summarization and retrieval.
    """
    if not text:
        return ""

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove excessive spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Fix broken line endings inside paragraphs
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Remove repeated spaces again after line join
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text and metadata from a PDF using PyMuPDF.

    Args:
        pdf_path (str): path to the PDF file

    Returns:
        dict: {
            "file_name": str,
            "file_path": str,
            "page_count": int,
            "raw_text": str,
            "clean_text": str
        }
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)

    all_text = []
    for page_num, page in enumerate(doc, start=1):
        page_text = page.get_text("text")
        if page_text.strip():
            all_text.append(f"\n\n--- Page {page_num} ---\n\n{page_text}")

    raw_text = "".join(all_text).strip()
    clean_text = clean_extracted_text(raw_text)

    result = {
        "file_name": pdf_file.name,
        "file_path": str(pdf_file),
        "page_count": len(doc),
        "raw_text": raw_text,
        "clean_text": clean_text,
    }

    doc.close()
    return result


def get_pdf_preview_text(clean_text: str, max_chars: int = 1500) -> str:
    """
    Return a preview snippet from extracted text for UI display.
    """
    if not clean_text:
        return ""

    return clean_text[:max_chars] + ("..." if len(clean_text) > max_chars else "")