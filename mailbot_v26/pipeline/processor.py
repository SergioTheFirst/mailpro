from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mailbot_v26.llm.summarizer import LLMSummarizer


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
        sender_line = (message.sender or "").strip() or account_login
        subject_line = (message.subject or "").strip()

        body_summary = self.llm.summarize_email(message.body or "")

        attachment_blocks: List[str] = []
        for att in message.attachments or []:
            text = (att.text or "").strip()
            if not text:
                continue
            kind = self._detect_attachment_kind(att.filename)
            summary = self.llm.summarize_attachment(text, kind=kind)
            if not summary:
                continue
            attachment_blocks.append("")
            attachment_blocks.append(att.filename or "attachment")
            attachment_blocks.append(summary)

        if not (subject_line or body_summary or attachment_blocks):
            return None

        lines: List[str] = [
            datetime.now().strftime("%H:%M %d.%m.%Y"),
            sender_line,
            subject_line,
            "",
        ]

        if body_summary:
            lines.append(body_summary)

        lines.extend(attachment_blocks)

        while lines and lines[-1] == "":
            lines.pop()

        return "\n".join(line for line in lines if line is not None)

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
