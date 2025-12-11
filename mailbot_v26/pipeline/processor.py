"""Pipeline processor with validation and final formatting."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from mailbot_v26.bot_core import validation
from mailbot_v26.config_loader import BotConfig
from mailbot_v26.state_manager import StateManager

_AMOUNT_RE = re.compile(r"(?P<amount>\d+[\d\s]*[\.,]?\d*)\s*(?P<currency>₽|руб|рублей|usd|eur|€|\$)?", re.IGNORECASE)
_DATE_RE = re.compile(r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})")
_ACTION_KEYWORDS = ["оплат", "оплатить", "подписать", "согласовать", "отправить", "доставить", "ожидается"]


@dataclass
class Message:
    subject: str
    body: str
    attachments: List[str] | None = None


@dataclass
class FactSummary:
    amount: Optional[str] = None
    date: Optional[str] = None
    action: Optional[str] = None
    doc_type: Optional[str] = None


class PipelineProcessor:
    """Sequential pipeline covering extraction→classification→validation."""

    def __init__(self, config: BotConfig, state: StateManager) -> None:
        self.config = config
        self.state = state

    def process(self, account_login: str, message: Message) -> str:
        text = self._extract_text(message)
        doc_type = self._classify(text)
        facts = self._extract_facts(text)
        facts.doc_type = doc_type
        facts = self._validate(facts, text)
        facts_line = self._facts_to_line(facts)
        validated = validation.validate_summary(facts_line, text)
        has_key_facts = any([facts.amount, facts.date, facts.action])
        fallback_summary = facts_line if facts_line and has_key_facts else None
        final_msg = build_final_message(message.subject, validated or fallback_summary)
        return final_msg

    def _extract_text(self, message: Message) -> str:
        parts: List[str] = [message.subject, message.body]
        if message.attachments:
            parts.extend(message.attachments)
        return "\n".join(filter(None, parts))

    def _classify(self, text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in ["счет", "счёт", "invoice", "к оплате"]):
            return "invoice"
        if any(word in lowered for word in ["договор", "contract"]):
            return "contract"
        if any(word in lowered for word in ["акт", "delivery", "отгруз"]):
            return "act"
        return "general"

    def _extract_facts(self, text: str) -> FactSummary:
        amount_match = _AMOUNT_RE.search(text)
        date_match = _DATE_RE.search(text)
        action = self._find_action(text)
        amount = None
        if amount_match:
            amount = amount_match.group("amount")
            currency = amount_match.group("currency")
            if currency:
                amount = f"{amount}{currency}".replace(" ", "")
        date_value = None
        if date_match:
            try:
                parsed = datetime.strptime(date_match.group(1), "%d.%m.%Y")
                date_value = parsed.strftime("%d.%m.%Y")
            except ValueError:
                date_value = date_match.group(1)
        return FactSummary(amount=amount, date=date_value, action=action)

    def _find_action(self, text: str) -> Optional[str]:
        lowered = text.lower()
        for keyword in _ACTION_KEYWORDS:
            if keyword in lowered:
                return keyword
        return None

    def _validate(self, facts: FactSummary, text: str) -> FactSummary:
        lowered = text.lower()
        if facts.action and any(neg in lowered for neg in ["не", "отмена", "cancel"]):
            facts.action = None
        return facts

    def _facts_to_line(self, facts: FactSummary) -> str:
        parts: List[str] = []
        if facts.amount:
            parts.append(f"СУММА: {facts.amount}")
        if facts.date:
            parts.append(f"СРОК: {facts.date}")
        if facts.action:
            parts.append(f"ДЕЙСТВИЕ: {facts.action}")
        if facts.doc_type:
            parts.append(f"ДОКУМЕНТ: {facts.doc_type}")
        return " | ".join(parts)


def build_final_message(subject: str, facts_str: str | None) -> str:
    facts_str = (facts_str or "").strip()
    if not facts_str:
        return ""

    clean_subject = (subject or "").strip()
    if clean_subject:
        base_message = f"SUBJECT: {clean_subject} | FACTS: {facts_str}"
    else:
        base_message = f"FACTS: {facts_str}"

    assert "none" not in base_message.lower()
    if len(base_message) > 240:
        return base_message[:240]
    return base_message


__all__ = ["PipelineProcessor", "Message", "FactSummary", "build_final_message"]


def _self_test_build_final_message():
    subject = "Оплата счёта"
    original = "Просим оплатить счёт №123 на сумму 150000 рублей до 20.12.2024"
    facts = "СУММА: 150000 | СРОК: 20.12.2024 | ДОКУМЕНТ: №123 | ДЕЙСТВИЕ: оплатить"

    valid = validation.validate_summary(facts, original)
    final = build_final_message(subject, valid)

    assert final.startswith("SUBJECT:")
    assert "none" not in final.lower()
    assert len(final) <= 240

    print("OK: build_final_message self-test passed")


if __name__ == "__main__":
    _self_test_build_final_message()
