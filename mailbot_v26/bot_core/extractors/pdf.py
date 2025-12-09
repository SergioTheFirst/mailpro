"""PDF text extraction using PyMuPDF."""
from __future__ import annotations

import fitz  # pymupdf


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF.

    Args:
        pdf_bytes: Raw PDF file content

    Returns:
        Extracted text or empty string if failed
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()

        full_text = "\n".join(text_parts).strip()
        return full_text

    except Exception:
        # Fail silently per CONSTITUTION Section VIII
        return ""


# Self-test
if __name__ == "__main__":
    # Create minimal PDF for testing
    test_doc = fitz.open()
    page = test_doc.new_page()
    page.insert_text((50, 50), "Test PDF content for MailBot v26")
    pdf_bytes = test_doc.write()
    test_doc.close()

    # Test extraction
    result = extract_pdf_text(pdf_bytes)
    assert "Test PDF content" in result
    print("✅ PDF extractor self-test PASSED")
