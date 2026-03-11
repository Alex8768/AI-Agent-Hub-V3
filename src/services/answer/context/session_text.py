"""Session-text helpers extracted from answer service."""

from __future__ import annotations

SESSION_MEMORY_MAX_CHARS = 4000


def clip_text(value: object, *, max_chars: int = SESSION_MEMORY_MAX_CHARS) -> str:
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
