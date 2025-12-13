from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mailbot_v26.llm.summarizer import LLMSummarizer

from mailbot_v26.text import clean_email_body, sanitize_text


@dataclass
class Attachment:
    filename: str
    content: bytes
    content_type: str = ""
    text: str | None = None


@dataclass
class InboundMessage:
    subject: str
    body: str
    sender: str = ""
    received_at: datetime | None = None
    attachments: List[Attachment] | None = None

    def __post_init__(self) -> None:
        if self.attachments is None:
            self.attachments = []


class MessageProcessor:
    """Single premium pipeline entry point."""

    def __init__(self, config, state) -> None:
        self.config = config
        self.state = state
        self.llm = LLMSummarizer(config.llm_call)

    def process(self, account_login: str, message: InboundMessage) -> Optional[str]:
        try:
            return self._build(account_login, message)
        except Exception:
            return None

    def _build(self, account_login: str, message: InboundMessage) -> Optional[str]:
        print("USING NEW PIPELINE")
        timestamp_line = self._format_timestamp(message.received_at)
        sender_line = sanitize_text((message.sender or "").strip() or account_login, max_len=200)
        subject_line = sanitize_text((message.subject or "Без темы").strip(), max_len=300)

        body_clean = clean_email_body(message.body or "")
        body_clean = sanitize_text(body_clean, max_len=6000)

        body_summary_raw = self.llm.summarize_email(body_clean)
        body_summary = sanitize_text(body_summary_raw, max_len=1200)
        if not self._is_meaningful(body_summary):
            body_summary = self._fallback_summary(body_clean)

        attachment_blocks: List[tuple[str, str]] = []
        for att in message.attachments or []:
            att_text = sanitize_text(att.text or "", max_len=4000)
            kind = self._detect_attachment_kind(att.filename)
            summary = ""
            if att_text:
                summary_raw = self.llm.summarize_attachment(att_text, kind=kind)
                summary = sanitize_text(summary_raw, max_len=1200)
                if not self._is_meaningful(summary):
                    summary = self._fallback_summary(att_text, limit=600)
            if not summary:
                summary = "Документ. Текст не извлечён."
            attachment_blocks.append((att.filename or "Вложение", summary))

        lines: List[str] = [timestamp_line, sender_line, subject_line, ""]

        if body_summary:
            lines.append(body_summary)

        for filename, block in attachment_blocks:
            lines.append("")
            lines.append(filename)
            lines.append(block)

        semantic_lines = [ln for ln in lines[3:] if ln.strip()]
        if len(semantic_lines) < 1:
            lines.append("")
            lines.append("Служебное письмо. Краткое содержание недоступно.")

        result = "\n".join(lines).strip()
        if len(result) > 3500:
            result = result[:3497] + "..."
        return result

    @staticmethod
    def _detect_attachment_kind(filename: str | None) -> str:
        if not filename:
            return "PDF"
        lower = filename.lower()
        if lower.endswith((".xls", ".xlsx")):
            return "EXCEL"
        if lower.endswith((".doc", ".docx")):
            return "CONTRACT"
        if lower.endswith(".pdf"):
            return "PDF"
        return "GENERIC"

    @staticmethod
    def _format_timestamp(received_at: datetime | None) -> str:
        dt = received_at or datetime.now()
        return dt.strftime("%H:%M %d.%m.%Y")

    @staticmethod
    def _is_meaningful(text: str, min_len: int = 15) -> bool:
        return bool(text and text.strip() and len(text.strip()) >= min_len)

    @staticmethod
    def _fallback_summary(text: str, limit: int = 700) -> str:
        sanitized = sanitize_text(text or "", max_len=limit + 200)
        if not sanitized:
            return "Содержание письма отсутствует."

        stripped = MessageProcessor._strip_greetings_and_signatures(sanitized)
        working = stripped or sanitized

        sentences = re.split(r"(?<=[.!?])\s+", working)
        meaningful: list[str] = []
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean.split()) < 3:
                continue
            meaningful.append(sentence_clean)
            if len(" ".join(meaningful)) >= limit:
                break

        if meaningful:
            summary = " ".join(meaningful[:3])
            if len(summary) > limit:
                summary = summary[: limit - 3] + "..."
            return summary

        truncated = working[: max(300, min(limit, 500))]
        if len(working) > len(truncated):
            truncated = truncated.rstrip() + "..."
        return truncated or "Содержание письма отсутствует."

    @staticmethod
    def _strip_greetings_and_signatures(text: str) -> str:
        greetings = (
            "hello",
            "hi",
            "добрый день",
            "здравствуйте",
            "привет",
            "уважаемый",
            "dear",
        )
        signatures = (
            "с уважением",
            "best regards",
            "regards",
            "cheers",
            "thanks",
            "thank you",
        )

        lines = text.split("\n")
        filtered_start: list[str] = []
        skip_prefix = True
        for line in lines:
            lower = line.strip().lower()
            if skip_prefix and lower and any(lower.startswith(g) for g in greetings):
                continue
            skip_prefix = False
            filtered_start.append(line)

        filtered_end: list[str] = []
        for line in reversed(filtered_start):
            lower = line.strip().lower()
            if lower and any(lower.startswith(s) for s in signatures):
                continue
            filtered_end.append(line)
        filtered_end.reverse()

        return "\n".join(filtered_end).strip()
