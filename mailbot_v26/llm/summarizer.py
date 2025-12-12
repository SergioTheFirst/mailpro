from typing import List, Callable, Optional

from mailbot_v26.llm.chunker import chunk_text
from mailbot_v26.llm import prompts_ru


class LLMSummarizer:

    def __init__(self, llm_call: Optional[Callable[[str], str]]):
        self.llm_call = llm_call

    def summarize_email(self, text: str) -> str:
        if not self.llm_call:
            return self._fallback(text)

        base = self._chunk_and_merge(
            text,
            prompts_ru.EMAIL_CHUNK,
            prompts_ru.EMAIL_MERGE,
        )

        prompt = self._select_final_prompt(base)
        return self.llm_call(prompt.format(summary=base)).strip()

    def summarize_attachment(self, text: str, kind: str = "PDF") -> str:
        if not self.llm_call:
            return self._fallback(text)

        chunk_prompt = {
            "PDF": prompts_ru.ATTACHMENT_CHUNK_PDF,
            "EXCEL": prompts_ru.ATTACHMENT_CHUNK_EXCEL,
            "CONTRACT": prompts_ru.ATTACHMENT_CHUNK_CONTRACT,
        }.get(kind, prompts_ru.ATTACHMENT_CHUNK_PDF)

        return self._chunk_and_merge(text, chunk_prompt, prompts_ru.ATTACHMENT_MERGE)

    def _chunk_and_merge(self, text: str, chunk_prompt: str, merge_prompt: str) -> str:
        chunks = chunk_text(text)
        if not chunks:
            return ""

        summaries: List[str] = []

        for ch in chunks:
            out = self.llm_call(chunk_prompt.format(text=ch))
            if out:
                summaries.append(out.strip())

        if not summaries:
            return ""

        return self.llm_call(
            merge_prompt.format(summaries="\n".join(summaries))
        ).strip()

    def _select_final_prompt(self, text: str) -> str:
        t = text.lower()

        for key, triggers in prompts_ru.TRIGGERS.items():
            if any(k in t for k in triggers):
                return prompts_ru.FINAL_PROMPTS.get(key)

        return prompts_ru.FINAL_PROMPTS["GENERIC"]

    def _fallback(self, text: str) -> str:
        """
        Fallback без LLM: тупо укороченный текст.
        """
        if not text:
            return ""
        text = text.strip()
        return text[:500] + ("..." if len(text) > 500 else "")
