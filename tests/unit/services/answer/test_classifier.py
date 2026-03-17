from __future__ import annotations

import pytest

from src.services.answer.classifier import QueryType, classify_query_type


@pytest.mark.asyncio
async def test_classifier_rules_dialog():
    qtype, reason = await classify_query_type(query="Привет, кто ты?", llm=None)
    assert qtype == QueryType.DIALOG
    assert reason.startswith("rules:")


@pytest.mark.asyncio
async def test_classifier_rules_advice():
    qtype, reason = await classify_query_type(query="Напиши код парсера PDF", llm=None)
    assert qtype == QueryType.ADVICE
    assert reason == "rules:advice_marker"


@pytest.mark.asyncio
async def test_classifier_rules_action():
    qtype, reason = await classify_query_type(query="Выполни команду ls", llm=None)
    assert qtype == QueryType.ACTION
    assert reason == "rules:action_marker"


@pytest.mark.asyncio
async def test_classifier_llm_fallback_for_ambiguous_query():
    class _LLM:
        async def generate(self, prompt: str) -> str:
            _ = prompt
            return "ADVICE"

    qtype, reason = await classify_query_type(query="Придумай сам", llm=_LLM())
    assert qtype == QueryType.ADVICE
    assert reason == "llm:advice"

