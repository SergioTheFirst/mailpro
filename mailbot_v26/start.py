"""Runtime orchestrator for MailBot Premium v26."""
from __future__ import annotations

import sys
import time
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message as EmailMessage
from pathlib import Path

if "__file__" not in globals():
    __file__ = str(Path("mailbot_v26/start.py").resolve())

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from mailbot_v26.config_loader import load_config
from mailbot_v26.imap_client import ResilientIMAP
from mailbot_v26.state_manager import StateManager
from mailbot_v26.pipeline.processor import Message, PipelineProcessor
from mailbot_v26.worker.telegram_sender import send_telegram


def _decode_subject(email_obj: EmailMessage) -> str:
    raw_subject = email_obj.get("Subject", "")
    try:
        return str(make_header(decode_header(raw_subject)))
    except Exception:
        return raw_subject or ""


def _extract_body(email_obj: EmailMessage) -> str:
    if email_obj.is_multipart():
        parts = []
        for part in email_obj.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                parts.append(payload.decode(charset, errors="ignore"))
            except Exception:
                continue
        return "\n".join(p.strip() for p in parts if p.strip())
    try:
        payload = email_obj.get_payload(decode=True) or b""
        charset = email_obj.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="ignore").strip()
    except Exception:
        return ""


def _parse_raw_email(raw_bytes: bytes) -> Message:
    email_obj = message_from_bytes(raw_bytes)
    subject = _decode_subject(email_obj)
    body = _extract_body(email_obj)
    return Message(subject=subject, body=body, attachments=None)


def main(config_dir: Path | None = None) -> None:
    config = load_config(config_dir or Path(__file__).resolve().parent / "config")
    state = StateManager()
    processor = PipelineProcessor(config=config, state=state)

    while True:
        for account in config.accounts:
            try:
                imap = ResilientIMAP(account, state)
                new_messages = imap.fetch_new_messages()
                for uid, raw in new_messages:
                    message = _parse_raw_email(raw)
                    final_text = processor.process(account.login, message)
                    if final_text:
                        send_telegram(
                            config.keys.telegram_bot_token,
                            account.telegram_chat_id,
                            final_text,
                        )
                state.save()
            except Exception as exc:  # Guaranteed Mode: keep other accounts alive
                state.set_imap_status(account.login, "error", str(exc))
                state.save()
                continue
        state.save()
        time.sleep(config.general.check_interval)


def _self_test():
    """
    Light self-test: import core components and ensure the main()
    function can be constructed without runtime import errors.
    """
    from mailbot_v26.config_loader import load_config  # noqa: F401
    from mailbot_v26.state_manager import StateManager  # noqa: F401
    from mailbot_v26.imap_client import ResilientIMAP  # noqa: F401
    from mailbot_v26.pipeline import processor  # noqa: F401
    from mailbot_v26.worker.telegram_sender import send_telegram  # noqa: F401

    print("✅ STEP 18: Imports OK, wiring seems consistent")


if __name__ == "__main__":
    _self_test()
