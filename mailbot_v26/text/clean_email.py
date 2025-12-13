from __future__ import annotations

import re

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
    "с уважением",
    "regards",
    "best regards",
    "--",
)


def _is_forward_start(line: str) -> bool:
    lower = line.strip().lower()
    return any(lower.startswith(marker) for marker in FORWARD_MARKERS)


def _is_signature_start(line: str) -> bool:
    lower = line.strip().lower()
    return any(lower.startswith(marker) for marker in SIGNATURE_MARKERS)


def clean_email_body(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if _is_forward_start(line):
            break
        if _is_signature_start(line):
            break
        cleaned_lines.append(line)

    collapsed: list[str] = []
    blank = False
    for line in cleaned_lines:
        stripped = line.rstrip()
        if stripped.strip() == "":
            if not blank:
                collapsed.append("")
            blank = True
            continue
        collapsed.append(stripped.strip())
        blank = False

    result = "\n".join(line for line in collapsed if line is not None)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result


__all__ = ["clean_email_body"]
