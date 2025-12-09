"""Core document processing pipeline for MailBot v26."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from ..config_loader import BotConfig
from ..formatter import format_summary
from ..state_manager import StateManager
from .classifier import classify_by_keywords
from .llm_client import CloudflareLLM
from .validator import validate_summary
from .validation import drop_none_tokens, ensure_length, is_confident_score


@dataclass
class Attachment:
    filename: str
    content: bytes
    content_type: str = ""


@dataclass
class InboundMessage:
    subject: str
    body: str
    attachments: List[Attachment]


_AMOUNT_RE = re.compile(r"(?P<amount>\d+[\d\s]*[\.,]?\d*)\s*(?P<currency>₽|руб|рублей|usd|eur|€|\$)?", re.IGNORECASE)
_DATE_RE = re.compile(r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})")


class MessageProcessor:
    """Sequential extraction → classification → fact validation."""

    def __init__(self, config: BotConfig, state: StateManager, base_dir: Path | None = None) -> None:
        self.config = config
        self.state = state
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.prompts_dir = self.base_dir.parent / "prompts"
        self.llm = CloudflareLLM(config.keys, state)
        self.prompt_extract = (self.prompts_dir / "extract_facts.txt").read_text(encoding="utf-8")
        self.prompt_verify = (self.prompts_dir / "verify_facts.txt").read_text(encoding="utf-8")

    def process(self, account_login: str, message: InboundMessage) -> str:
        text = self._collect_text(message)
        doc_type, score = classify_by_keywords(
            filename=" ".join(att.filename for att in message.attachments),
            text_sample=text,
        )
        if not is_confident_score(score):
            doc_type = doc_type or "general"
        extracted = self._extract_facts(text)
        verified = self._verify_facts(extracted, text)
        validated = validate_summary(verified or extracted, text)
        cleaned = validated or drop_none_tokens(verified or extracted)
        clipped = ensure_length(cleaned or message.subject)
        if doc_type and cleaned:
            clipped = ensure_length(f"{clipped} | #{doc_type}")
        return format_summary([clipped])

    def _collect_text(self, message: InboundMessage) -> str:
        parts = [message.subject, message.body]
        parts.extend(self._extract_attachments(message.attachments))
        return "\n".join(part for part in parts if part)

    def _extract_attachments(self, attachments: Iterable[Attachment]) -> List[str]:
        texts: List[str] = []
        for attachment in attachments:
            text = self._extract_by_type(attachment)
            if text:
                texts.append(text)
        return texts

    def _extract_by_type(self, attachment: Attachment) -> str:
        name_lower = attachment.filename.lower()
        from .extractors.pdf import extract_pdf_text  # lazy import
        from .extractors.doc import extract_docx_text
        from .extractors.excel import extract_excel_text

        if name_lower.endswith(".pdf"):
            return extract_pdf_text(attachment.content)
        if name_lower.endswith(".docx"):
            return extract_docx_text(attachment.content)
        if name_lower.endswith(".xls") or name_lower.endswith(".xlsx"):
            return extract_excel_text(attachment.content)
        try:
            return attachment.content.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _extract_facts(self, text: str) -> str:
        llm_result = self.llm.ask(self.prompt_extract, text)
        if llm_result:
            return llm_result
        return self._fallback_fact_scan(text)

    def _fallback_fact_scan(self, text: str) -> str:
        amount_match = _AMOUNT_RE.search(text)
        date_match = _DATE_RE.search(text)
        parts: List[str] = []
        if amount_match:
            amount = amount_match.group("amount")
            currency = amount_match.group("currency") or ""
            parts.append(f"СУММА: {amount}{currency}")
        if date_match:
            parts.append(f"СРОК: {date_match.group(1)}")
        return " | ".join(parts) if parts else ""

    def _verify_facts(self, facts_line: str, text: str) -> str:
        if not facts_line:
            return ""
        verify_prompt = self.prompt_verify.format(original_text=text, extracted_facts=facts_line)
        verified = self.llm.ask(verify_prompt, "Проверить факты")
        return verified or facts_line


__all__ = ["MessageProcessor", "Attachment", "InboundMessage"]
