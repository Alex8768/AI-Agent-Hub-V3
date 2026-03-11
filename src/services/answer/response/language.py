"""Language helpers extracted from answer service."""

from __future__ import annotations


def detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"


def normalize_language_tag(language: str, *, query: str = "") -> str:
    value = str(language or "").strip().lower()
    if value in {"ru", "en"}:
        return value
    return detect_response_language(query)


def answer_language(answer: str) -> str:
    text = str(answer or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"
