"""Validation helpers for post-LLM cleaning."""
from __future__ import annotations

from typing import List


def drop_none_tokens(facts_line: str) -> str:
    """Remove NONE tokens and trim separators."""
    if not facts_line:
        return ""
    tokens = [token.strip() for token in facts_line.split("|") if token.strip()]
    filtered = [t for t in tokens if t.lower() != "none"]
    return " | ".join(filtered).strip()


def ensure_length(text: str, limit: int = 200) -> str:
    """Trim text to the Constitution limit."""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" |")


def is_confident_score(score: float) -> bool:
    return score >= 0.7


__all__ = ["drop_none_tokens", "ensure_length", "is_confident_score"]
