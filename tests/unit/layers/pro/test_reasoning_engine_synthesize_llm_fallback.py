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
                {"type": "chunk", "id": "c1", "source_refs": ["doc:Z#9"], "confidence": 0.7},
            ],
        }


class _FailingLLM:
    async def generate(self, prompt: str) -> str:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_synthesize_falls_back_when_llm_fails():
    eng = ReasoningEngine(retriever=_FakeRetriever(), llm=_FailingLLM())

    req = AnswerRequest(query="Q?")
    resp = await eng.synthesize(req)

    # fallback answer is deterministic stub
    assert resp.answer == "(reasoning layer stub)"

    # evidence-derived fields still computed
    assert resp.context_preview == "doc:Z#9"
    assert resp.confidence == 0.7
    assert len(resp.provenance) == 1
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    assert diag.get("planner_path_used") is False
    es = dict(diag.get("evidence_summary") or {})
    assert es.get("count") == 1
    assert (es.get("origin_counts") or {}).get("vector") == 1
