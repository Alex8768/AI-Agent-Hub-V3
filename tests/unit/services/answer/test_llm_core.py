from __future__ import annotations

import pytest

from src.services.answer.llm_core import LLMCoreMode, generate_with_llm_core


@pytest.mark.asyncio
async def test_llm_core_returns_candidate_when_guard_passes():
    class _LLM:
        async def generate(self, prompt: str) -> str:
            _ = prompt
            return "Краткий план по теме презентации: цель, структура, вывод."

    result = await generate_with_llm_core(
        query="План презентации по степям Краснодарского края",
        llm=_LLM(),
        mode=LLMCoreMode.ADVICE,
        instruction="Give structured answer",
        context={"language": "ru"},
        quality_guard=lambda candidate: "план" in candidate.lower(),
    )
    assert "план" in result.lower()


@pytest.mark.asyncio
async def test_llm_core_uses_custom_emergency_fallback_when_guard_rejects():
    class _LLM:
        async def generate(self, prompt: str) -> str:
            _ = prompt
            return "I am here to help."

    result = await generate_with_llm_core(
        query="Что ты умеешь?",
        llm=_LLM(),
        mode=LLMCoreMode.DIALOG,
        instruction="No templates",
        context={"language": "ru"},
        quality_guard=lambda _: False,
        max_retries=2,
        emergency_fallback=lambda _: "fallback-value",
    )
    assert result == "fallback-value"


@pytest.mark.asyncio
async def test_llm_core_can_disable_default_fallback():
    result = await generate_with_llm_core(
        query="ambiguous",
        llm=None,
        mode=LLMCoreMode.DIALOG,
        instruction="",
        allow_default_fallback=False,
    )
    assert result == ""

