"""Language helpers extracted from answer service."""

from __future__ import annotations


def detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    lowered = text.lower()
    if any(token in lowered for token in [" der ", " die ", " das ", " und ", " ist ", "nicht", "über"]):
        return "de"
    if any(token in lowered for token in [" le ", " la ", " les ", " et ", " est ", "avec", "pour", "présentation"]):
        return "fr"
    return "en"


def normalize_language_tag(language: str, *, query: str = "") -> str:
    value = str(language or "").strip().lower()
    if value in {"ru", "en", "de", "fr"}:
        return value
    return detect_response_language(query)


def answer_language(answer: str) -> str:
    text = str(answer or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    lowered = text.lower()
    if any(token in lowered for token in [" der ", " die ", " das ", " und ", " ist ", "nicht", "über"]):
        return "de"
    if any(token in lowered for token in [" le ", " la ", " les ", " et ", " est ", "avec", "pour", "présentation"]):
        return "fr"
    return "en"
