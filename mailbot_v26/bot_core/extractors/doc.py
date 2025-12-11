from __future__ import annotations

import io


def _load_docx_parser():
    try:
        from docx import Document  # type: ignore

        return Document
    except Exception:
        return None


def _load_docx2txt():
    try:
        import docx2txt  # type: ignore

        return docx2txt
    except Exception:
        return None


def extract_doc(file_bytes: bytes, filename: str) -> str:
    name = (filename or "").lower()

    if name.endswith((".docx", ".docm")):
        document_cls = _load_docx_parser()
        if document_cls is None:
            return ""
        try:
            doc = document_cls(io.BytesIO(file_bytes))
            return "\n".join(
                p.text for p in doc.paragraphs if p.text and p.text.strip()
            )
        except Exception:
            return ""

    if name.endswith(".doc"):
        docx2txt = _load_docx2txt()
        if docx2txt is None:
            return ""
        try:
            return docx2txt.process(io.BytesIO(file_bytes))
        except Exception:
            return ""

    return ""


extract_docx_text = extract_doc
