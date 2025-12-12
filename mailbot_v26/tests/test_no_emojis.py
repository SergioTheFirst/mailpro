from pathlib import Path

import mailbot_v26.llm.prompts_ru as prompts_ru

EMOJI_RANGES = [
    (0x1F300, 0x1F5FF),
    (0x1F600, 0x1F64F),
    (0x1F680, 0x1F6FF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0x1F900, 0x1F9FF),
    (0x1FA70, 0x1FAFF),
]


def _contains_emoji(text: str) -> bool:
    for char in text:
        code = ord(char)
        if any(start <= code <= end for start, end in EMOJI_RANGES):
            return True
    return False


def test_prompts_have_no_emoji():
    content = Path(prompts_ru.__file__).read_text(encoding="utf-8")
    assert not _contains_emoji(content)


def test_repository_has_no_emoji():
    root = Path(__file__).resolve().parents[1]
    for path in root.rglob("*.py"):
        if any(part in {"venv", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not _contains_emoji(text), f"Emoji found in {path}"
