"""Runtime orchestrator for MailBot Premium v26.

This module wires together configuration loading, IMAP ingestion,
message processing, Telegram delivery, and state persistence. It must
remain resilient (Guaranteed Mode) and never crash the whole runtime
because of a single failing account.
"""
from __future__ import annotations

import logging
import sys
import time
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message as EmailMessage
from pathlib import Path
from typing import List

if "__file__" not in globals():
    __file__ = str(Path("mailbot_v26/start.py").resolve())

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from mailbot_v26.config_loader import BotConfig, GeneralConfig, KeysConfig, load_config
from mailbot_v26.imap_client import ResilientIMAP
from mailbot_v26.state_manager import StateManager
from mailbot_v26.bot_core.message_processor import (
    Attachment,
    InboundMessage,
    MessageProcessor,
)
from mailbot_v26.worker.telegram_sender import send_telegram


CURRENT_DIR = Path(__file__).resolve().parent
LOG_PATH = CURRENT_DIR / "mailbot.log"


def _configure_logging() -> None:
    handlers: List[logging.Handler] = []
    try:
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
            handlers.append(file_handler)
        except OSError as exc:
            print(f"File logging unavailable at {LOG_PATH}: {exc}")
        handlers.append(logging.StreamHandler(sys.stdout))
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=handlers,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        print(f"Logging setup failed; continuing with stdout only: {exc}")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )


def _build_safe_config() -> BotConfig:
    general = GeneralConfig(check_interval=180, max_attachment_mb=15, admin_chat_id="")
    return BotConfig(
        general=general,
        accounts=[],
        keys=KeysConfig(telegram_bot_token="", cf_account_id="", cf_api_token=""),
    )


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
                text = payload.decode(charset, errors="ignore")
                if text.strip():
                    parts.append(text.strip())
            except Exception:
                continue
        return "\n".join(parts)
    try:
        payload = email_obj.get_payload(decode=True) or b""
        charset = email_obj.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="ignore").strip()
    except Exception:
        return ""


def _extract_attachments(email_obj: EmailMessage, max_mb: int) -> List[Attachment]:
    attachments: List[Attachment] = []
    byte_limit = max_mb * 1024 * 1024
    for part in email_obj.walk():
        disposition = part.get_content_disposition()
        filename = part.get_filename()
        if disposition != "attachment" and not filename:
            continue
        try:
            payload = part.get_payload(decode=True) or b""
            if byte_limit > 0 and len(payload) > byte_limit:
                continue
            attachments.append(
                Attachment(
                    filename=filename or "attachment.bin",
                    content=payload,
                    content_type=part.get_content_type() or "",
                )
            )
        except Exception:
            continue
    return attachments


def _parse_raw_email(raw_bytes: bytes, config: BotConfig) -> InboundMessage:
    email_obj = message_from_bytes(raw_bytes)
    subject = _decode_subject(email_obj)
    body = _extract_body(email_obj)
    attachments = _extract_attachments(email_obj, config.general.max_attachment_mb)
    return InboundMessage(subject=subject, body=body, attachments=attachments)


def main(config_dir: Path | None = None) -> None:
    _configure_logging()
    logger = logging.getLogger("mailbot")

    print("MailBot v26 starting")
    try:
        base_config_dir = config_dir or CURRENT_DIR / "config"
        config = load_config(base_config_dir)
        logger.info("Configuration loaded for %d accounts", len(config.accounts))
        print(f"Loaded configuration for {len(config.accounts)} accounts")
    except Exception as exc:
        logger.exception("Failed to load configuration from %s", config_dir or CURRENT_DIR / "config")
        print(f"Configuration could not be loaded: {exc}")
        config = _build_safe_config()
        print("Using safe defaults; no accounts configured")

    state = StateManager()
    print("State manager ready")
    processor = MessageProcessor(config=config, state=state)
    print("Message processor ready")

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"Cycle {cycle} start")
            logger.info("Cycle %d started", cycle)
            if not config.accounts:
                logger.warning("No accounts configured; sleeping")
            for account in config.accounts:
                try:
                    imap = ResilientIMAP(account, state)
                    new_messages = imap.fetch_new_messages()
                    logger.info(
                        "Account %s fetched %d messages", account.login, len(new_messages)
                    )
                    for uid, raw in new_messages:
                        inbound = _parse_raw_email(raw, config)
                        try:
                            final_text = processor.process(account.login, inbound)
                        except Exception:
                            logger.exception("Processor failed for UID %s", uid)
                            continue
                        if not final_text:
                            continue
                        try:
                            ok = send_telegram(
                                config.keys.telegram_bot_token,
                                account.telegram_chat_id,
                                final_text,
                            )
                        except Exception:
                            logger.exception("Telegram send crashed for UID %s", uid)
                            ok = False
                        logger.info(
                            "Telegram send for UID %s: %s", uid, "ok" if ok else "fail"
                        )
                        if not ok:
                            print(
                                "Telegram send failed; check token, chat_id, or network."
                            )
                    try:
                        state.save()
                    except Exception:
                        logger.exception("State save failed after account %s", account.login)
                except Exception:
                    logger.exception("Account loop failed for %s", account.login)
                    try:
                        state.save()
                    except Exception:
                        logger.exception("State save failed after account error %s", account.login)
                    continue
            try:
                state.save()
            except Exception:
                logger.exception("State save failed after cycle %d", cycle)
            delay = max(1, min(config.general.check_interval, 180))
            time.sleep(delay)
    except KeyboardInterrupt:
        logger.info("Graceful shutdown requested (KeyboardInterrupt)")
    except Exception:
        logger.exception("Fatal error in main loop (Guaranteed Mode)")


if __name__ == "__main__":
    main()
