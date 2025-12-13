from __future__ import annotations

import re
from typing import Any

FORWARD_MARKERS = (
    "from:",
    "sent:",
    "to:",
    "subject:",
    "от:",
    "кому:",
    "тема:",
    "отправлено:",
    "-----original message-----",
    "----- forwarded message -----",
)

SIGNATURE_MARKERS = (
    "с уважением,",
    "regards,",
)


def _to_str(text: Any) -> str:
    if text is None:
        return ""
    try:
        return str(text)
    except Exception:
        return ""


def _is_forward_start(line: str) -> bool:
    lower = line.strip().lower()
    if lower.startswith("--"):
        return True
    return any(lower.startswith(marker) for marker in FORWARD_MARKERS)


def _is_signature_start(line: str) -> bool:
    lower = line.strip().lower()
    if lower.startswith("--"):
        return True
    return any(lower.startswith(marker) for marker in SIGNATURE_MARKERS)


def clean_email_body(text: Any) -> str:
    try:
        normalized = _to_str(text).replace("\r\n", "\n").replace("\r", "\n")
    except Exception:
        return ""

    lines = normalized.split("\n")
    cleaned: list[str] = []

    for line in lines:
        if _is_forward_start(line):
            break
        if _is_signature_start(line):
            break
        cleaned.append(line)

    collapsed: list[str] = []
    blank = False
    for line in cleaned:
        stripped = line.strip()
        if not stripped:
            if blank:
                continue
            collapsed.append("")
            blank = True
            continue
        collapsed.append(stripped)
        blank = False

    result = "\n".join(collapsed).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


__all__ = ["clean_email_body"]
