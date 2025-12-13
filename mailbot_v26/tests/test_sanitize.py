from mailbot_v26.text.sanitize import sanitize_text


def test_sanitize_removes_png_chunks():
    raw = """header
IHDR garbage bytes
valid line
IDAT more bytes"""
    cleaned = sanitize_text(raw)
    assert "IHDR" not in cleaned
    assert "IDAT" not in cleaned
    assert "valid line" in cleaned


def test_sanitize_removes_zip_headers():
    raw = "First line\nPK\u0000\u0001 binary data\nNext"  # noqa: W605
    cleaned = sanitize_text(raw)
    assert "PK" not in cleaned
    assert "Next" in cleaned


def test_sanitize_removes_encoded_headers():
    raw = "=?koi8-r?B?abcd?=\nUseful text"
    cleaned = sanitize_text(raw)
    assert "koi8" not in cleaned.lower()
    assert "Useful text" in cleaned


def test_sanitize_preserves_russian_text():
    raw = "Основной текст письма без мусора"
    cleaned = sanitize_text(raw)
    assert cleaned == raw


def test_sanitize_removes_base64_runs():
    raw = "Header\n" + ("Q" * 50)
    cleaned = sanitize_text(raw)
    assert "Q" * 30 not in cleaned
