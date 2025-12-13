import mailbot_v26.start as start
from mailbot_v26.pipeline.processor import Attachment


def test_png_attachment_extraction_is_empty():
    data = b"\x89PNG\r\n\x1a\nIHDRbinarydata"
    att = Attachment(filename="image.png", content=data, content_type="image/png")
    text = start._extract_attachment_text(att)
    assert text == ""


def test_zip_like_attachment_not_leaking_pk():
    data = b"PK\x03\x04fakezipdata"
    att = Attachment(filename="file.docx", content=data, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    text = start._extract_attachment_text(att)
    assert "PK" not in text
    assert text in {"", None}
