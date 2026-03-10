from __future__ import annotations


def _detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"


def _normalize_language_tag(language: str, *, query: str = "") -> str:
    value = str(language or "").strip().lower()
    if value in {"ru", "en"}:
        return value
    return _detect_response_language(query)


def _answer_language(answer: str) -> str:
    text = str(answer or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"


def build_assistant_fallback_answer(*, query: str, language: str) -> str:
    _ = query
    if language == "ru":
        return (
            "Привет! Я готов помочь как ассистент по рабочим задачам. "
            "Могу подготовить план, черновики и следующие шаги по вашему запросу. "
            "Если хотите точный ответ по внутренним данным, загрузите документы или уточните контекст."
        )
    return (
        "Hi! I can help as an operations assistant. "
        "I can prepare a plan, drafts, and next steps for your request. "
        "If you need a source-grounded answer from internal data, upload documents or provide more context."
    )


def is_simple_greeting_query(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    return (
        "привет" in lowered
        or lowered.startswith("hi")
        or "hello" in lowered
    )


def is_unknown_style_answer(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "извините, я не знаю",
        "я не знаю",
        "i don't know",
        "i do not know",
        "sorry, i don't know",
    ]
    return any(marker in lowered for marker in markers)


def is_generic_assistant_fallback_answer(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    if not lowered:
        return False
    return (
        "готов помочь как ассистент" in lowered
        or "i can help as an operations assistant" in lowered
    )


async def build_assistant_chat_recovery_answer(
    *,
    query: str,
    language: str,
    llm: object | None,
    current_answer: str,
) -> str:
    target_language = _normalize_language_tag(language, query=query)
    current = str(current_answer or "").strip()
    if (
        current
        and not is_unknown_style_answer(current)
        and not is_generic_assistant_fallback_answer(current)
        and _answer_language(current) == target_language
    ):
        return current

    if llm is not None and hasattr(llm, "generate"):
        prompt = (
            "You are a helpful operations assistant. "
            "The user asked a conversational question with low evidence context. "
            "Answer naturally in the user's language in 1-3 short sentences. "
            "Do not say you don't know. "
            f"User query: {str(query or '').strip()}"
        )
        try:
            candidate = str(await llm.generate(prompt)).strip()
        except Exception:
            candidate = ""
        if (
            candidate
            and not is_unknown_style_answer(candidate)
            and _answer_language(candidate) == target_language
        ):
            return candidate

    if target_language == "ru":
        return (
            "Да, конечно. Я рядом и готова помогать по задачам шаг за шагом: "
            "разобрать запрос, предложить понятный план и аккуратно довести до результата."
        )
    return (
        "Absolutely. I am here to help step by step: "
        "clarify your request, propose a clear plan, and move it forward safely."
    )
