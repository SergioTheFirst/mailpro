"""Legacy formatter disabled; use mailbot_v26.pipeline.processor instead."""

from __future__ import annotations


def format_summary(parts):
    """Legacy formatter is no longer used."""
    raise RuntimeError("Legacy formatter disabled; use mailbot_v26.pipeline.processor")


__all__ = ["format_summary"]
