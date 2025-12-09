import importlib.util

requests_spec = importlib.util.find_spec("requests")
if requests_spec is not None:
    import requests  # type: ignore
else:
    requests = None


def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False

    if requests is None:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": text[:4000]}

    try:
        resp = requests.post(url, data=data, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def _self_test():
    # We cannot hit real Telegram here.
    # Just test that empty text is not sent.
    assert send_telegram("dummy", "123", "") is False
    assert send_telegram("dummy", "123", "   ") is False
    print("✅ STEP 17: telegram_sender self-test PASSED (logic only)")


if __name__ == "__main__":
    _self_test()
