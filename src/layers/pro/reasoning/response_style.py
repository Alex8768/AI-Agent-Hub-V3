from __future__ import annotations


def _detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    lowered = text.lower()
    if any(token in lowered for token in [" der ", " die ", " das ", " und ", " ist ", "nicht", "über"]):
        return "de"
    if any(token in lowered for token in [" le ", " la ", " les ", " et ", " est ", "avec", "pour", "présentation"]):
        return "fr"
    return "en"


def _normalize_language_tag(language: str, *, query: str = "") -> str:
    value = str(language or "").strip().lower()
    if value in {"ru", "en", "de", "fr"}:
        return value
    return _detect_response_language(query)


def _answer_language(answer: str) -> str:
    text = str(answer or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    lowered = text.lower()
    if any(token in lowered for token in [" der ", " die ", " das ", " und ", " ist ", "nicht", "über"]):
        return "de"
    if any(token in lowered for token in [" le ", " la ", " les ", " et ", " est ", "avec", "pour", "présentation"]):
        return "fr"
    return "en"


def build_assistant_fallback_answer(*, query: str, language: str) -> str:
    target_language = _normalize_language_tag(language, query=query)
    if is_simple_greeting_query(query):
        if target_language == "ru":
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

    return build_safe_terminal_response(
        query=query,
        language=target_language,
        current_answer="",
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


def is_capability_check_query(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "готов",
        "можешь",
        "можете",
        "ты тут",
        "can you",
        "are you ready",
    ]
    return any(marker in lowered for marker in markers)


def is_ambiguous_reference_query(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    pronouns = [
        "они",
        "он",
        "она",
        "это",
        "эти",
        "туда",
        "там",
        "them",
        "it",
        "those",
    ]
    token_count = len([t for t in lowered.replace("?", " ").split() if t.strip()])
    return token_count <= 8 and any(p in lowered for p in pronouns)


def is_substantive_query(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    token_count = len([t for t in lowered.replace("?", " ").split() if t.strip()])
    if token_count >= 7:
        return True
    if any(marker in lowered for marker in ["план", "структур", "outline", "plan", "proposal", "steps"]):
        return True
    return is_knowledge_query(lowered)


def is_knowledge_query(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "что ты знаешь о",
        "расскажи о",
        "объясни",
        "what do you know about",
        "tell me about",
        "explain",
    ]
    return any(marker in lowered for marker in markers)


def is_speculative_answer(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "может быть",
        "возможно",
        "скорее всего",
        "вероятно",
        "maybe",
        "probably",
        "possibly",
    ]
    return any(marker in lowered for marker in markers)


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


def is_reasoning_stub_answer(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    return lowered in {"(reasoning layer stub)", "(no answer generated)", ""}


def is_template_like_answer(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    if not lowered:
        return True
    markers = [
        "я готов помочь как ассистент по рабочим задачам",
        "i can help as an operations assistant",
        "я рядом и готова помогать по задачам шаг за шагом",
        "i am here to help step by step",
        "готова помочь. если дадите тему или цель",
        "ready to help. share your topic or goal",
    ]
    return any(marker in lowered for marker in markers)


def is_destructive_request(query: str) -> bool:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return False
    markers = [
        "удалить",
        "delete",
        "rm -rf",
        "truncate",
        "drop table",
        "wipe",
        "destroy",
        "erase",
    ]
    return any(marker in lowered for marker in markers)


def build_helpful_safe_alternative(*, query: str, language: str, current_answer: str = "") -> str:
    return build_safe_terminal_response(
        query=query,
        language=language,
        current_answer=current_answer,
    )


def build_safe_terminal_response(
    *,
    query: str,
    language: str,
    current_answer: str = "",
) -> str:
    target_language = _normalize_language_tag(language, query=query)
    current = str(current_answer or "").strip()
    if current and not is_reasoning_stub_answer(current):
        return current

    if is_destructive_request(query):
        if target_language == "ru":
            return (
                "Я не могу помогать с удалением всех файлов или другими разрушительными действиями. "
                "Если хотите, предложу безопасный вариант: сначала инвентаризация, бэкап и точечные изменения по подтвержденному списку."
            )
        return (
            "I cannot help with deleting all files or other destructive actions. "
            "If useful, I can suggest a safe workflow first: inventory, backup, and targeted changes on an explicit approved list."
        )

    if is_substantive_query(query):
        return normalize_low_evidence_friendliness(
            query=query,
            language=target_language,
            answer="",
        )
    if is_knowledge_query(query):
        if target_language == "ru":
            return (
                "Могу дать краткий обзор темы и структуру для углубления:\n"
                "1) Ключевое определение и контекст\n"
                "2) Основные характеристики и примеры\n"
                "3) Важные факторы и последствия\n"
                "4) Короткий вывод и что изучить дальше"
            )
        return (
            "I can provide a short topic overview plus a structure for deeper study:\n"
            "1) Core definition and context\n"
            "2) Main characteristics and examples\n"
            "3) Key factors and implications\n"
            "4) Brief takeaway and what to explore next"
        )

    if is_capability_check_query(query) or is_simple_greeting_query(query):
        if target_language == "ru":
            return (
                "Помогаю с практическими задачами: разбор запроса, структурирование ответа, план действий и аккуратная доработка шаг за шагом. "
                "Могу начать с короткого плана под вашу текущую задачу."
            )
        return (
            "I can help with practical tasks: clarify your request, structure an answer, and propose step-by-step next actions. "
            "I can start with a short plan for your current goal."
        )

    if is_ambiguous_reference_query(query):
        if target_language == "ru":
            return (
                "Могу помочь, но сейчас не хватает контекста, чтобы ответить точно. "
                "Уточните объект или цель, и я сразу дам полезный структурный ответ."
            )
        return (
            "I can help, but there is not enough context to answer precisely yet. "
            "Clarify the target or goal and I will provide a useful structured response."
        )

    if target_language == "ru":
        return (
            "Готова помочь. Если дадите тему или цель, сразу предложу компактный план и следующие шаги."
        )
    return "Ready to help. Share your topic or goal and I will provide a compact plan with next steps."


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
            "Do not invent facts. "
            "If context is ambiguous, explicitly ask for clarification. "
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


def normalize_low_evidence_friendliness(
    *,
    query: str,
    language: str,
    answer: str,
) -> str:
    """Normalize low-evidence responses to a friendly deterministic style."""
    target_language = _normalize_language_tag(language, query=query)
    current = str(answer or "").strip()
    if (
        current
        and not is_unknown_style_answer(current)
        and not is_speculative_answer(current)
        and _answer_language(current) == target_language
        and not is_ambiguous_reference_query(query)
    ):
        return current
    if is_simple_greeting_query(query):
        return build_assistant_fallback_answer(query=query, language=target_language)
    if is_substantive_query(query):
        if current and not is_generic_assistant_fallback_answer(current):
            return current
        if target_language == "ru":
            return (
                "Вот безопасный базовый план, который можно сразу использовать и уточнять по вашим материалам:\n"
                "1) Введение и цель\n"
                "2) Ключевые блоки темы\n"
                "3) Факты и примеры\n"
                "4) Выводы и практическая ценность\n"
                "Если нужно, адаптирую структуру под конкретный формат (школа, вуз, бизнес)."
            )
        if target_language == "de":
            return (
                "Hier ist ein sicherer Basisplan, den wir direkt verwenden und dann anpassen koennen:\n"
                "1) Einleitung und Ziel\n"
                "2) Kernabschnitte des Themas\n"
                "3) Fakten und Beispiele\n"
                "4) Fazit und praktische Bedeutung\n"
                "Wenn Sie moechten, passe ich die Struktur an Ihr konkretes Format an."
            )
        if target_language == "fr":
            return (
                "Voici un plan de base, utile et sans risque, que nous pouvons affiner ensuite :\n"
                "1) Introduction et objectif\n"
                "2) Sections principales du sujet\n"
                "3) Faits et exemples\n"
                "4) Conclusion et valeur pratique\n"
                "Je peux ensuite adapter la structure a votre format exact."
            )
        return (
            "Here is a safe baseline plan you can use immediately and refine with your data:\n"
            "1) Introduction and goal\n"
            "2) Core topic sections\n"
            "3) Facts and examples\n"
            "4) Conclusion and practical value\n"
            "If needed, I can tailor this structure to your exact format."
        )
    if is_capability_check_query(query):
        if target_language == "ru":
            return (
                "Да, конечно. Я рядом и готова помочь. "
                "Можем вместе уточнить задачу и сразу наметить понятные шаги."
            )
        return (
            "Absolutely. I am here to help. "
            "We can clarify your goal and map clear next steps right away."
        )
    if is_ambiguous_reference_query(query):
        if target_language == "ru":
            return (
                "Сейчас в контексте не хватает точной опоры, чтобы уверенно сказать, о ком или о чем идет речь. "
                "Уточните, кого именно вы имеете в виду, и я отвечу строго по данным без догадок."
            )
        return (
            "There is not enough context to determine who or what you refer to with confidence. "
            "Please clarify the subject, and I will answer strictly from available evidence."
        )
    if target_language == "ru":
        return (
            "Да, конечно. Я рядом и готова помочь. "
            "Можем вместе уточнить задачу и сразу наметить понятные шаги."
        )
    return (
        "Absolutely. I am here to help. "
        "We can clarify your goal and map clear next steps right away."
    )
