"""
Keyword-based document classifier for MailBot Premium v26.
Complies with CONSTITUTION.md Section III.4.a.
"""
from __future__ import annotations

from typing import Optional, Tuple

# Document type keywords (Russian + English)
KEYWORDS = {
    "invoice": [
        "счет", "счёт", "invoice", "оплата", "накладная", "bill",
        "payment", "акт", "к оплате",
    ],
    "contract": [
        "договор", "agreement", "контракт", "contract", "соглашение",
    ],
    "payment_request": [
        "оплатить", "срочно оплатить", "просим оплатить",
        "request for payment", "payment due",
    ],
    "claim": [
        "претензия", "рекламация", "complaint", "claim",
        "возражение", "несогласие",
    ],
    "delivery_act": [
        "акт выполненных работ", "акт приёмки", "ксу", "ksu",
        "act of acceptance", "delivery note",
    ],
    "bank_statement": [
        "выписка", "statement", "bank statement", "движение средств",
    ],
    "specification": [
        "спецификация", "specification", "перечень товаров", "спецификация",
    ],
    "legal_notice": [
        "уведомление", "требование", "legal notice",
        "demand letter", "судебное",
    ],
    "hr_doc": [
        "приказ", "заявление", "order", "увольнение",
        "отпуск", "hr", "кадры",
    ],
    "scanned": [
        "scan", "скан", ".jpg", ".jpeg", ".png", ".tiff",
        "фото", "image",
    ],
}


def classify_by_keywords(
    filename: str,
    text_sample: str,
    content_type: str = "",
) -> Tuple[Optional[str], float]:
    """
    Fast keyword-based classification.

    Args:
        filename: Attachment filename
        text_sample: First ~500 chars of extracted text
        content_type: MIME type

    Returns:
        (document_type, confidence_score)
        Returns (None, 0.0) if no match

    Confidence scale:
        0.9-1.0: Multiple strong matches
        0.7-0.9: Single strong match
        0.5-0.7: Weak match
        < 0.5: Uncertain (should use LLM fallback)
    """
    filename_lower = (filename or "").lower()
    text_lower = (text_sample or "")[:500].lower()
    content_type_lower = (content_type or "").lower()

    search_text = f"{filename_lower} {text_lower} {content_type_lower}"

    scores: dict[str, float] = {}
    for doc_type, keywords in KEYWORDS.items():
        matches = 0
        for keyword in keywords:
            if keyword in search_text:
                matches += 1

        if matches > 0:
            if matches >= 3:
                scores[doc_type] = 0.95
            elif matches == 2:
                scores[doc_type] = 0.85
            elif matches == 1:
                scores[doc_type] = 0.70

    if not scores:
        return (None, 0.0)

    best_type = max(scores, key=scores.get)
    confidence = scores[best_type]

    return (best_type, confidence)


def _self_test() -> bool:
    """Internal self-test."""

    result = classify_by_keywords(
        filename="invoice_123.pdf",
        text_sample="Счёт на оплату 150000 рублей. Просим оплатить до 20.12.2024",
    )
    assert result[0] == "invoice" or result[0] == "payment_request"
    assert result[1] >= 0.70

    result = classify_by_keywords(
        filename="agreement_2024.docx",
        text_sample="Договор №123/45 на оказание услуг",
    )
    assert result[0] == "contract"
    assert result[1] >= 0.70

    result = classify_by_keywords(
        filename="scan_20241209.jpg",
        text_sample="",
        content_type="image/jpeg",
    )
    assert result[0] == "scanned"

    result = classify_by_keywords(
        filename="unknown.txt",
        text_sample="Just some random text without keywords",
    )
    assert result[0] is None
    assert result[1] == 0.0

    result = classify_by_keywords(
        filename="contract_and_invoice.pdf",
        text_sample="Договор №1. Счёт на оплату. К оплате 100000.",
    )
    assert result[0] in ["invoice", "contract", "payment_request"]
    assert result[1] >= 0.85

    return True


if __name__ == "__main__":
    if _self_test():
        print("\n✅ Keyword classifier self-test PASSED (5/5 tests)")
