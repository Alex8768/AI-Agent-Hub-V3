from __future__ import annotations

import asyncio
import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _FakeRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [
                {"type": "chunk", "id": "c1", "source_refs": ["doc:T#1"], "confidence": 0.4},
            ],
        }


class _SlowLLM:
    async def generate(self, prompt: str) -> str:
        await asyncio.sleep(0.2)
        return "TOO_SLOW"


@pytest.mark.asyncio
async def test_synthesize_times_out_and_falls_back():
    eng = ReasoningEngine(retriever=_FakeRetriever(), llm=_SlowLLM(), llm_timeout_s=0.01)

    req = AnswerRequest(query="Q?")
    resp = await eng.synthesize(req)

    assert resp.answer != "(reasoning layer stub)"
    assert str(resp.answer).strip()
    assert resp.context_preview == "doc:T#1"
    assert resp.confidence == 0.4
