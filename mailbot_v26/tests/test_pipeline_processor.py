from pathlib import Path

from mailbot_v26.config_loader import load_config
from mailbot_v26.pipeline.processor import Message, PipelineProcessor
from mailbot_v26.state_manager import StateManager


def test_pipeline_generates_compact_summary(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.ini").write_text("""[general]\ncheck_interval=100\nmax_attachment_mb=10\nadmin_chat_id=1\n""", encoding="utf-8")
    (config_dir / "accounts.ini").write_text("""[acc]\nlogin=a@b.com\npassword=p\nhost=imap\nuse_ssl=true\ntelegram_chat_id=1\n""", encoding="utf-8")
    (config_dir / "keys.ini").write_text("""[telegram]\nbot_token=t\n\n[cloudflare]\naccount_id=c\napi_token=k\n""", encoding="utf-8")

    config = load_config(config_dir)
    processor = PipelineProcessor(config, StateManager(tmp_path / "state.json"))
    summary = processor.process(
        account_login=config.accounts[0].login,
        message=Message(subject="Счет 321", body="Оплатить 12000 руб до 01.01.2025"),
    )
    assert summary.startswith("SUBJECT:")
    assert "none" not in summary.lower()
    assert len(summary) <= 240


def test_pipeline_falls_back_to_subject_when_no_facts(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.ini").write_text("""[general]\ncheck_interval=100\nmax_attachment_mb=10\nadmin_chat_id=1\n""", encoding="utf-8")
    (config_dir / "accounts.ini").write_text("""[acc]\nlogin=a@b.com\npassword=p\nhost=imap\nuse_ssl=true\ntelegram_chat_id=1\n""", encoding="utf-8")
    (config_dir / "keys.ini").write_text("""[telegram]\nbot_token=t\n\n[cloudflare]\naccount_id=c\napi_token=k\n""", encoding="utf-8")
    config = load_config(config_dir)

    processor = PipelineProcessor(config, StateManager(tmp_path / "state.json"))
    summary = processor.process(
        account_login=config.accounts[0].login,
        message=Message(subject="Обновление", body="Привет"),
    )
    assert summary == ""
