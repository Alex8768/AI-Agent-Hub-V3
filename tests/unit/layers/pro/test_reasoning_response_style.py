from __future__ import annotations

import pytest


def test_normalize_low_evidence_friendliness_rewrites_unknown_russian():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Ты готова помогать?",
        language="ru",
        answer="Извините, я не знаю.",
    )
    assert "Да, конечно" in out


def test_normalize_low_evidence_friendliness_preserves_valid_answer():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Hi there",
        language="en",
        answer="Absolutely, I can help you with that.",
    )
    assert out == "Absolutely, I can help you with that."


def test_normalize_low_evidence_friendliness_rewrites_ambiguous_reference_query():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Как они туда попали?",
        language="ru",
        answer="Может быть, они воспользовались транспортом.",
    )
    lowered = out.lower()
    assert "уточните" in lowered
    assert "без догадок" in lowered


def test_normalize_low_evidence_friendliness_builds_safe_outline_for_substantive_query():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Сделай структуру презентации про climate change для 7 класса с примерами и выводами",
        language="ru",
        answer="",
    )
    lowered = out.lower()
    assert "безопасный базовый план" in lowered
    assert "1)" in lowered


def test_normalize_low_evidence_friendliness_preserves_substantive_nonfallback_answer():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    answer = "Step 1: Define scope. Step 2: Gather examples. Step 3: Build final outline."
    out = normalize_low_evidence_friendliness(
        query="Build an outline for a short deck about climate change impacts and mitigation",
        language="en",
        answer=answer,
    )
    assert out == answer


def test_build_safe_terminal_response_capability_is_structured():
    from src.layers.pro.reasoning.response_style import build_safe_terminal_response

    out = build_safe_terminal_response(
        query="Что ты умеешь?",
        language="ru",
        current_answer="",
    )
    lowered = out.lower()
    assert "1)" in lowered
    assert "план" in lowered


def test_build_safe_terminal_response_uses_topic_hint_for_generic_query():
    from src.layers.pro.reasoning.response_style import build_safe_terminal_response

    out = build_safe_terminal_response(
        query="Нужна помощь с презентацией по истории",
        language="ru",
        current_answer="",
    )
    lowered = out.lower()
    assert "по теме" in lowered
    assert "презентацией по истории" in lowered


def test_is_low_information_answer_detects_insufficient_info_phrases():
    from src.layers.pro.reasoning.response_style import is_low_information_answer

    assert is_low_information_answer("Извините, но у меня недостаточно информации, чтобы ответить на этот вопрос.")
    assert is_low_information_answer("Извините, но предоставленный контекст недостаточен для ответа.")
    assert is_low_information_answer("There is not enough information to answer this question.")
    assert not is_low_information_answer("Вот план: 1) цель, 2) структура, 3) черновик.")


def test_build_safe_terminal_response_identity_query_is_not_generic():
    from src.layers.pro.reasoning.response_style import build_safe_terminal_response

    out = build_safe_terminal_response(
        query="Кто ты?",
        language="ru",
        current_answer="",
    )
    lowered = out.lower()
    assert "ai-ассистент" in lowered or "ассистент" in lowered
    assert "цели" in lowered or "задач" in lowered


@pytest.mark.asyncio
async def test_build_natural_safe_terminal_response_prefers_llm_candidate():
    from src.layers.pro.reasoning.response_style import build_natural_safe_terminal_response

    class _LLM:
        async def generate(self, prompt: str) -> str:
            _ = prompt
            return "Вот короткий рабочий план: 1) цель, 2) структура, 3) первый черновик."

    out = await build_natural_safe_terminal_response(
        query="Сделай план ответа",
        language="ru",
        llm=_LLM(),
        risk_tier="L1",
        current_answer="",
    )
    assert "рабочий план" in out.lower()


@pytest.mark.asyncio
async def test_build_natural_safe_terminal_response_l2_requires_confirm_semantics():
    from src.layers.pro.reasoning.response_style import build_natural_safe_terminal_response

    class _LLM:
        async def generate(self, prompt: str) -> str:
            _ = prompt
            return "План готов; перед выполнением действий требуется подтверждение."

    out = await build_natural_safe_terminal_response(
        query="Выполни команду ls",
        language="ru",
        llm=_LLM(),
        risk_tier="L2",
        current_answer="fallback",
    )
    assert "подтверждение" in out.lower()


@pytest.mark.asyncio
async def test_build_natural_safe_terminal_response_retries_after_template_candidate():
    from src.layers.pro.reasoning.response_style import build_natural_safe_terminal_response

    class _LLM:
        def __init__(self):
            self.calls = 0

        async def generate(self, prompt: str) -> str:
            _ = prompt
            self.calls += 1
            if self.calls == 1:
                return "Ready to help. Share your goal and target format."
            return "По презентации по истории: сначала цель, затем структура слайда, затем черновик вывода."

    llm = _LLM()
    out = await build_natural_safe_terminal_response(
        query="Нужна помощь с презентацией по истории",
        language="ru",
        llm=llm,
        risk_tier="L1",
        current_answer="",
    )
    assert "презентации по истории" in out.lower()
    assert llm.calls >= 2
