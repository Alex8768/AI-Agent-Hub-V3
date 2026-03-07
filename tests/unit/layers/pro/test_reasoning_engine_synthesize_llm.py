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
        # think_node expects JSON action output
        if "Output format:" in prompt:
            return '{"plan":["SEARCH","ANSWER"],"reason":"Need evidence then answer"}'
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
    assert any("doc:X#1" in p for p in llm.prompts)  # retrieval context reaches answer prompt
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    assert "fallback_reason" not in diag
    assert "agent_iterations" in diag
    assert "agent_current_action" in diag
    assert "agent_current_step" in diag
    assert diag.get("planner_path_used") is True
    assert diag.get("evidence_contract_version") == "v1"
    es = dict(diag.get("evidence_summary") or {})
    assert es.get("count") == 1
    assert (es.get("origin_counts") or {}).get("vector") == 1
    ec = dict(diag.get("evidence_contract") or {})
    assert ec.get("version") == "v1"
    assert ec.get("total") == 1
    assert ec.get("with_source_refs") == 1
    assert ec.get("with_known_origin") == 1
    assert ec.get("valid_minimal") is True
