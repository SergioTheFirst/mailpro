import logging
from types import SimpleNamespace

import pytest

from mailbot_v26.worker import telegram_sender


class DummyResponse:
    def __init__(self, status_code: int = 200, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text
        self.content = text.encode()


def test_send_telegram_empty_text_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        assert telegram_sender.send_telegram("token", "chat", "") is False
    assert "empty" in caplog.text.lower()


def test_send_telegram_success(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    def fake_post(url: str, data: dict, timeout: int) -> DummyResponse:
        called["url"] = url
        called["data"] = data
        called["timeout"] = timeout
        return DummyResponse(status_code=200, text="ok")

    monkeypatch.setattr(telegram_sender, "requests", SimpleNamespace(post=fake_post))
    assert telegram_sender.send_telegram("token", "123", "hello") is True
    assert called["data"]["text"] == "hello"
    assert called["data"]["chat_id"] == "123"


def test_send_telegram_non_200_logs(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(
        telegram_sender,
        "requests",
        SimpleNamespace(post=lambda url, data, timeout: DummyResponse(status_code=500, text="bad")),
    )
    with caplog.at_level(logging.ERROR):
        assert telegram_sender.send_telegram("token", "123", "hello") is False
    assert "status 500" in caplog.text


def test_send_telegram_exception(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def raising_post(url: str, data: dict, timeout: int) -> DummyResponse:
        raise RuntimeError("network error")

    monkeypatch.setattr(telegram_sender, "requests", SimpleNamespace(post=raising_post))
    with caplog.at_level(logging.ERROR):
        assert telegram_sender.send_telegram("token", "123", "hello") is False
    assert "network error" in caplog.text


def test_send_telegram_requests_missing(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(telegram_sender, "requests", None)
    with caplog.at_level(logging.ERROR):
        assert telegram_sender.send_telegram("token", "123", "hello") is False
    assert "requests library is not available" in caplog.text
