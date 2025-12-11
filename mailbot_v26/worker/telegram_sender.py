import importlib.util
import logging
from typing import Any

requests_spec = importlib.util.find_spec("requests")
if requests_spec is not None:
    import requests  # type: ignore
else:
    requests = None


def _get_logger() -> logging.Logger:
    return logging.getLogger(__name__)


def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    logger = _get_logger()
    text = (text or "").strip()
    if not text:
        logger.error("Telegram message text is empty; skipping send")
        return False

    if requests is None:
        logger.error("requests library is not available; cannot send Telegram message")
        return False

    token = (bot_token or "").strip()
    target_chat = (chat_id or "").strip()
    if not token:
        logger.error("Telegram bot token is empty or invalid")
        return False
    if not target_chat:
        logger.error("Telegram chat_id is empty or invalid")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": target_chat, "text": text[:4000]}

    try:
        resp = requests.post(url, data=data, timeout=10)
    except Exception as exc:  # pragma: no cover - network errors
        logger.exception("Telegram request failed: %s", exc)
        return False

    if resp.status_code != 200:
        body: Any = getattr(resp, "text", None) or getattr(resp, "content", b"")
        logger.error("Telegram returned status %s with body: %s", resp.status_code, body)
        return False

    return True


def _self_test():
    # We cannot hit real Telegram here.
    # Just test that empty text is not sent.
    assert send_telegram("dummy", "123", "") is False
    assert send_telegram("dummy", "123", "   ") is False
    print("OK: telegram_sender self-test passed (logic only)")


if __name__ == "__main__":
    _self_test()
