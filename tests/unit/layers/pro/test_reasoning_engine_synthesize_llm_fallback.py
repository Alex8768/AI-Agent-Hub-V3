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
    assert diag.get("evidence_contract_version") == "v1"
    assert diag.get("evidence_contract_valid_minimal") is True
    assert diag.get("evidence_contract_missing_minimal_fields") == []
    es = dict(diag.get("evidence_summary") or {})
    assert es.get("count") == 1
    assert (es.get("origin_counts") or {}).get("vector") == 1
    ec = dict(diag.get("evidence_contract") or {})
    assert ec.get("version") == "v1"
    mr = dict(ec.get("minimal_requirements") or {})
    assert mr.get("min_total") == 1
    assert mr.get("requires_source_refs") is True
    assert mr.get("requires_known_origin") is True
    assert ec.get("total") == 1
    assert ec.get("with_source_refs") == 1
    assert ec.get("with_known_origin") == 1
    assert ec.get("source_refs_coverage") == 1.0
    assert ec.get("known_origin_coverage") == 1.0
    assert ec.get("reliability_coverage") == 1.0
    assert ec.get("missing_minimal_fields") == []
    assert ec.get("valid_minimal") is True


class _EmptyRetriever:
    async def retrieve(self, request):
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


@pytest.mark.asyncio
async def test_synthesize_sets_warning_when_evidence_contract_invalid():
    eng = ReasoningEngine(retriever=_EmptyRetriever(), llm=_FailingLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))

    diag = dict(getattr(resp, "diagnostics", {}) or {})
    ec = dict(diag.get("evidence_contract") or {})
    assert diag.get("evidence_contract_valid_minimal") is False
    assert diag.get("evidence_contract_missing_minimal_fields") == ["source_refs", "origin"]
    assert ec.get("source_refs_coverage") == 0.0
    assert ec.get("known_origin_coverage") == 0.0
    assert ec.get("reliability_coverage") == 0.0
    assert ec.get("missing_minimal_fields") == ["source_refs", "origin"]

    warnings = list(getattr(resp, "warnings", []) or [])
    assert "evidence_contract_minimal_invalid" in warnings
