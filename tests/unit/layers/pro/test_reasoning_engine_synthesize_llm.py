from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _FakeRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [
                {"type": "chunk", "id": "c1", "source_refs": ["doc:X#1"], "confidence": 0.6},
            ],
        }


class _FakeLLM:
    def __init__(self):
        self.prompts = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "LLM_ANSWER"


@pytest.mark.asyncio
async def test_synthesize_uses_llm_when_injected():
    retriever = _FakeRetriever()
    llm = _FakeLLM()
    eng = ReasoningEngine(retriever=retriever, llm=llm)

    req = AnswerRequest(query="Q?")
    resp = await eng.synthesize(req)

    assert resp.answer == "LLM_ANSWER"
    assert llm.prompts, "LLM should have been called"
    assert "Question: Q?" in llm.prompts[0]
    assert "Context:" in llm.prompts[0]
    assert "doc:X#1" in llm.prompts[0]  # provenance/preview makes it into prompt
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    assert "agent_current_action" in diag
    assert "agent_current_step" in diag
