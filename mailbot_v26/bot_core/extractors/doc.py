"""DOCX text extraction using mammoth."""
from __future__ import annotations

from io import BytesIO

import mammoth


def extract_docx_text(docx_bytes: bytes) -> str:
    """
    Extract text from DOCX.

    Args:
        docx_bytes: Raw DOCX file content

    Returns:
        Extracted text or empty string if failed
    """
    try:
        result = mammoth.extract_raw_text(BytesIO(docx_bytes))
        return result.value.strip()
    except Exception:
        return ""


# Self-test
if __name__ == "__main__":
    # We can't easily create DOCX in self-test without python-docx
    # But we can verify the function exists and handles errors
    try:
        result = extract_docx_text(b"invalid docx data")
        assert result == ""  # Should fail gracefully
        print("✅ DOCX extractor self-test PASSED (error handling verified)")
    except Exception:
        print("❌ DOCX extractor failed unexpectedly")
