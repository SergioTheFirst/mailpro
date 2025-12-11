"""
Local fact validation for MailBot Premium v26.
Complies with CONSTITUTION.md Section VI.
"""
from __future__ import annotations

import re
from typing import Optional


def clean_none(text: str) -> str:
    """
    Remove any segment containing NONE.

    Per CONSTITUTION Section VI.1: "Удалять любые сегменты, содержащие NONE"
    """
    if not text or text.strip().upper() == "NONE":
        return ""

    segments = text.split("|")
    cleaned = [seg.strip() for seg in segments if "NONE" not in seg.upper()]
    return " | ".join(cleaned)


def validate_numbers(summary: str, original_text: str) -> bool:
    """Check if all numbers in summary exist in original text."""
    summary_numbers = set(re.findall(r"\d+", summary))
    if not summary_numbers:
        return True

    original_numbers = set(re.findall(r"\d+", original_text))
    return summary_numbers.issubset(original_numbers)


def validate_dates(summary: str, original_text: str) -> bool:
    """Check if all dates in summary exist in original text."""
    date_pattern = r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    summary_dates = set(re.findall(date_pattern, summary))
    if not summary_dates:
        return True

    original_dates = set(re.findall(date_pattern, original_text))
    for date in summary_dates:
        norm_date = date.replace("/", ".").replace("-", ".")
        if not any(norm_date == o.replace("/", ".").replace("-", ".") for o in original_dates):
            return False
    return True


def check_negation(text: str, fact: str) -> bool:
    """Check if a fact is negated in the original text."""
    if not fact:
        return False

    text_lower = text.lower()
    fact_lower = fact.lower()
    if fact_lower not in text_lower:
        return False

    fact_pos = text_lower.find(fact_lower)
    window_start = max(0, fact_pos - 50)
    context = text_lower[window_start:fact_pos]
    negations = ["не", "нет", "ни", "без", "отказ", "отмена", "cancel"]
    return any(neg in context for neg in negations)


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def validate_summary(summary: str, original_text: str, min_similarity: float = 0.35) -> Optional[str]:
    """
    Comprehensive validation of LLM summary.

    Returns validated summary or None if validation fails.
    """
    if not summary or summary.strip().upper() == "NONE":
        return None

    cleaned = clean_none(summary)
    if not cleaned:
        return None

    if not validate_numbers(cleaned, original_text):
        return None

    if not validate_dates(cleaned, original_text):
        return None

    action_match = re.search(r"ДЕЙСТВИЕ:\s*(\w+)", cleaned, re.IGNORECASE)
    if action_match and check_negation(original_text, action_match.group(1)):
        cleaned = re.sub(r"\|\s*ДЕЙСТВИЕ:[^|]+", "", cleaned).strip().strip("|").strip()
        if not cleaned:
            return None

    similarity = jaccard_similarity(cleaned, original_text)
    if similarity < min_similarity:
        return None

    return cleaned


# Self-test

def _self_test() -> bool:
    result = clean_none("A: 100 | B: NONE | C: test")
    assert result == "A: 100 | C: test"

    assert validate_numbers("Оплатить 150000", "Сумма 150000 рублей") is True
    assert validate_numbers("Оплатить 999000", "Сумма 150000 рублей") is False

    assert validate_dates("До 20.12.2024", "Срок оплаты: 20.12.2024") is True
    assert validate_dates("До 99.99.9999", "Срок оплаты: 20.12.2024") is False

    assert check_negation("Не оплачивать счёт", "оплачивать") is True
    assert check_negation("Срочно оплатить", "оплатить") is False

    sim = jaccard_similarity("оплатить 100 руб", "просим оплатить 100 руб до")
    assert sim > 0.5

    original = "Просим оплатить счёт №123 на сумму 150000 рублей до 20.12.2024"
    good_summary = "СУММА: 150000 | СРОК: 20.12.2024 | ДОКУМЕНТ: №123"
    bad_summary = "СУММА: 999000 | СРОК: 01.01.9999 | ДОКУМЕНТ: №999"

    assert validate_summary(good_summary, original) is not None
    assert validate_summary(bad_summary, original) is None

    print("✅ VALIDATOR SELF-TEST PASSED")
    return True


if __name__ == "__main__":
    _self_test()
