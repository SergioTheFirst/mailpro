"""Lightweight end-to-end pipeline skeleton.

The implementation is intentionally deterministic so it can run in
resource-constrained environments while respecting the Constitution's
pipeline order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from ..config_loader import BotConfig
from ..formatter import format_summary
from ..state_manager import StateManager

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
        validated = self._validate(facts, text)
        return self._format_output(validated, message.subject)

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
        # Remove obviously contradicted facts (simple negation check)
        lowered = text.lower()
        if facts.action and any(neg in lowered for neg in ["не", "отмена", "cancel"]):
            facts.action = None
        return facts

    def _format_output(self, facts: FactSummary, subject: str) -> str:
        parts: List[str] = []
        if facts.amount:
            parts.append(f"💰{facts.amount}")
        if facts.date:
            parts.append(f"📅{facts.date}")
        if facts.action:
            parts.append(f"▶{facts.action}")
        if not parts:
            parts.append(subject.strip())
        if facts.doc_type and parts:
            parts.append(f"#{facts.doc_type}")
        return format_summary(parts)


__all__ = ["PipelineProcessor", "Message", "FactSummary"]
