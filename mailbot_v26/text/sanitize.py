from __future__ import annotations

import re


BINARY_MARKERS = (
    "ihdr",
    "idat",
    "pk",
    "content_types",
    "base64",
    "=?koi8",
    "image001.png",
)

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def _contains_marker(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in BINARY_MARKERS)


def _has_dense_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    printable = sum(1 for ch in stripped if ch.isprintable())
    if printable == 0:
        return True
    letters_digits = sum(1 for ch in stripped if ch.isalpha() or ch.isdigit())
    if len(stripped) > 80 and letters_digits < len(stripped) * 0.25:
        return True
    if re.search(r"[^\w\s]{12,}", stripped):
        return True
    return False


def _strip_control(text: str) -> str:
    return CONTROL_CHARS_RE.sub(" ", text.replace("\x00", " "))


def sanitize_text(text: str, max_length: int = 4000) -> str:
    if not text:
        return ""

    safe_lines = []
    for raw_line in text.splitlines():
        line = _strip_control(raw_line)
        if _contains_marker(line) or _has_dense_noise(line):
            continue
        safe_lines.append(line)

    cleaned = "\n".join(safe_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if len(cleaned) > max_length:
        return cleaned[:max_length]
    return cleaned


__all__ = ["sanitize_text"]
