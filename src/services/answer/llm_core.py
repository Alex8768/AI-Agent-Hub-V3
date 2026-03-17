from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class LLMCoreMode(str, Enum):
    DIALOG = "dialog"
    ADVICE = "advice"
    ACTION = "action"


def _detect_language(text: str) -> str:
    value = str(text or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in value):
        return "ru"
    return "en"


def _build_mode_directive(mode: LLMCoreMode) -> str:
    if mode == LLMCoreMode.ACTION:
        return (
            "Mode: ACTION. Provide preparation-only guidance, never claim execution happened, "
            "and keep explicit confirmation-before-execution semantics."
        )
    if mode == LLMCoreMode.ADVICE:
        return "Mode: ADVICE. Provide a useful structured answer with practical next steps."
    return "Mode: DIALOG. Provide concise natural conversational answer."


def _default_emergency_fallback(*, query: str, mode: LLMCoreMode, language: str) -> str:
    q = str(query or "").strip()
    if language == "ru":
        if mode == LLMCoreMode.ACTION:
            return (
                "Сделаем безопасно: сначала подготовлю план/черновик, "
                "а любые действия — только после вашего подтверждения."
            )
        if mode == LLMCoreMode.ADVICE:
            return (
                f"По запросу ({q[:80]}) предложу рабочий путь: "
                "цель, шаги, первый черновик результата."
            )
        return (
            f"Поняла запрос ({q[:80]}). "
            "Сформулируйте цель чуть точнее, и я сразу дам короткий полезный ответ."
        )
    if mode == LLMCoreMode.ACTION:
        return (
            "Safe approach: I can prepare a plan/draft first, and any execution requires your confirmation."
        )
    if mode == LLMCoreMode.ADVICE:
        return f"For this request ({q[:80]}), I can provide goal, steps, and a first draft."
    return f"I got your request ({q[:80]}). Share the exact goal and I will answer concisely."


async def generate_with_llm_core(
    *,
    query: str,
    llm: object | None,
    mode: LLMCoreMode | str,
    instruction: str,
    context: dict[str, object] | None = None,
    quality_guard: Callable[[str], bool] | None = None,
    max_retries: int = 1,
    emergency_fallback: Callable[[str], str] | None = None,
    allow_default_fallback: bool = True,
) -> str:
    """Unified generation-first wrapper with bounded retries and emergency fallback."""
    resolved_mode = mode if isinstance(mode, LLMCoreMode) else LLMCoreMode(str(mode or "dialog").lower())
    query_text = str(query or "").strip()
    language = str((context or {}).get("language") or _detect_language(query_text)).strip().lower() or "en"

    if llm is not None and hasattr(llm, "generate"):
        retries = max(1, int(max_retries))
        for attempt in range(retries):
            prompt = (
                "You are an operations AI assistant. "
                "Answer naturally in the user's language. "
                "Avoid canned assistant boilerplate and avoid fabrications. "
                "Reference at least one concrete term from the user query. "
                f"{_build_mode_directive(resolved_mode)} "
                f"Instruction: {str(instruction or '').strip()} "
                f"Attempt: {attempt}. "
                f"User query: {query_text}"
            )
            try:
                candidate = str(await llm.generate(prompt)).strip()
            except Exception:
                candidate = ""
            if not candidate:
                continue
            if quality_guard is None or bool(quality_guard(candidate)):
                return candidate

    if emergency_fallback is not None:
        fallback = str(emergency_fallback(query_text)).strip()
        if fallback:
            return fallback
    if not bool(allow_default_fallback):
        return ""
    return _default_emergency_fallback(
        query=query_text,
        mode=resolved_mode,
        language=language,
    )

