"""Output formatting for compact Telegram-friendly summaries."""

from __future__ import annotations

from typing import Iterable

MAX_LEN = 200


def _trim_segment(segment: str) -> str:
    return segment.strip().replace("\n", " ")


def format_summary(parts: Iterable[str]) -> str:
    filtered = [_trim_segment(p) for p in parts if p and p.strip().upper() != "NONE"]
    summary = " | ".join(filtered)
    return summary[:MAX_LEN]


__all__ = ["format_summary", "MAX_LEN"]
