from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from mailbot_v26.bot_core.message_processor import InboundMessage, Attachment
from mailbot_v26.llm.summarizer import LLMSummarizer


class MessageProcessor:
    """
    Премиум-обработка писем:
    - чанкинг
    - управляемые промпты
    - краткий деловой вывод
    """

    def __init__(self, config, state):
        self.config = config
        self.state = state

        # llm_call должен уже быть определён в проекте (Cloudflare, OpenAI и т.д.)
        self.llm = LLMSummarizer(config.llm_call)

    def process(self, account_login: str, message: InboundMessage) -> Optional[str]:
        try:
            return self._build(account_login, message)
        except Exception:
            return None

    def _build(self, account_login: str, message: InboundMessage) -> Optional[str]:
        lines: List[str] = []

        lines.append(datetime.now().strftime("%H:%M %d.%m.%Y"))
        lines.append(account_login)

        if message.subject:
            lines.append(message.subject.strip())

        body_summary = self.llm.summarize_email(message.body)
        if body_summary:
            lines.append("")
            lines.append(body_summary)

        for att in message.attachments or []:
            text = getattr(att, "text", "")
            if not text:
                continue

            summary = self.llm.summarize_attachment(text)
            if not summary:
                continue

            lines.append("")
            lines.append(att.filename)
            lines.append(summary)

        if len(lines) < 2:
            return None

        return "\n".join(lines)
