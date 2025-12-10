

from __future__ import annotations
import io
from docx import Document
import docx2txt


def extract_doc(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()

    # DOCX — быстрый безопасный путь
    if name.endswith((".docx", ".docm")):
        try:
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(
                p.text for p in doc.paragraphs if p.text and p.text.strip()
            )
        except Exception:
            return ""

    # DOC — через docx2txt
    if name.endswith(".doc"):
        try:
            return docx2txt.process(io.BytesIO(file_bytes))
        except Exception:
            return ""

    return ""


extract_docx_text = extract_doc
