from mailbot_v26.text.clean_email import clean_email_body


def test_clean_email_removes_forward_headers():
    body = (
        "Главный текст письма\n"
        "Дополнительная строка\n"
        "From: someone@example.com\n"
        "Sent: Monday\n"
        "Subject: test\n"
        "To: person\n"
        "Rest of quoted"
    )
    cleaned = clean_email_body(body)
    assert "Главный текст письма" in cleaned
    assert "Дополнительная строка" in cleaned
    assert "From:" not in cleaned
    assert "Sent:" not in cleaned
    assert "Subject:" not in cleaned
    assert "To:" not in cleaned


def test_clean_email_removes_signature_block():
    body = (
        "Основной текст\n"
        "С уважением,\n"
        "Имя\n"
        "Телефон"
    )
    cleaned = clean_email_body(body)
    assert cleaned == "Основной текст"
