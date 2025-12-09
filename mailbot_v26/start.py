"""Entry point for MailBot Premium v26.

This script wires together configuration loading, state management and a
single pass of the pipeline. Network calls are avoided during local
development; IMAPClient usage is encapsulated inside ``ResilientIMAP``
and can be mocked in tests.
"""

from __future__ import annotations

from pathlib import Path

from .config_loader import BotConfig, ConfigError, load_config
from .pipeline.processor import Message, PipelineProcessor
from .state_manager import StateManager


def build_processor(config_dir: Path | None = None) -> tuple[BotConfig, PipelineProcessor]:
    config = load_config(config_dir or Path(__file__).resolve().parent / "config")
    state = StateManager()
    processor = PipelineProcessor(config=config, state=state)
    return config, processor


def demo_run() -> str:
    config, processor = build_processor()
    account = config.accounts[0]
    message = Message(
        subject="Счет на оплату №123",
        body="Просим оплатить 150000 руб до 20.12.2024",
    )
    summary = processor.process(account.login, message)
    return summary


if __name__ == "__main__":
    try:
        print(demo_run())
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
