from types import SimpleNamespace

from mailbot_v26.pipeline import processor
from mailbot_v26.pipeline.processor import Attachment, InboundMessage, MessageProcessor


class DummyState:
    def save(self) -> None:
        return None


def test_message_processor_formats_output(monkeypatch):
    class DummySummarizer:
        def __init__(self, _):
            pass

        def summarize_email(self, text: str) -> str:
            return "Email summary"

        def summarize_attachment(self, text: str, kind: str = "PDF") -> str:
            return f"Attachment summary {kind}"

    monkeypatch.setattr(processor, "LLMSummarizer", DummySummarizer)

    cfg = SimpleNamespace(llm_call=lambda x: "ok")
    msg = InboundMessage(
        subject="Subject line",
        sender="sender@example.com",
        body="body text",
        attachments=[Attachment(filename="file.pdf", content=b"data", text="content")],
    )

    output = MessageProcessor(cfg, DummyState()).process("login", msg)
    assert output is not None
    lines = output.split("\n")
    assert len(lines) >= 6
    assert lines[1] == "sender@example.com"
    assert lines[2] == "Subject line"
    assert "Email summary" in output
    assert "file.pdf" in output
    assert "Attachment summary PDF" in output


def test_message_processor_handles_empty(monkeypatch):
    monkeypatch.setattr(processor, "LLMSummarizer", lambda cfg: SimpleNamespace(
        summarize_email=lambda text: "",
        summarize_attachment=lambda text, kind="PDF": "",
    ))

    cfg = SimpleNamespace(llm_call=None)
    msg = InboundMessage(subject="", sender="", body="", attachments=[])
    assert MessageProcessor(cfg, DummyState()).process("account", msg) is None
