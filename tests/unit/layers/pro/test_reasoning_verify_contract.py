from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _PlannerRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [
                {"type": "chunk", "id": "c1", "source_refs": ["doc:V#1"], "confidence": 0.9},
            ],
        }


class _PlannerLLM:
    async def generate(self, prompt: str) -> str:
        if "Output format:" in prompt:
            return '{"plan":["SEARCH","ANSWER"],"reason":"need evidence then answer"}'
        return "VERIFY_OK"


class _FallbackRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [
                # Missing source_refs -> self_check warn -> verify warn.
                {"type": "chunk", "id": "c-no-refs", "confidence": 0.4},
            ],
        }


class _FailingLLM:
    async def generate(self, prompt: str) -> str:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_verify_contract_is_stable_on_planner_path():
    eng = ReasoningEngine(retriever=_PlannerRetriever(), llm=_PlannerLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    verify = dict(diag.get("verify") or {})
    assert verify.get("version") == "v1"
    assert verify.get("status") == "pass"
    assert verify.get("reasons") == []
    assert verify.get("policy_mode") == "warning_only"

    inputs = dict(verify.get("inputs") or {})
    assert set(inputs.keys()) == {
        "planner_path_used",
        "self_check_status",
        "self_check_policy_mode",
        "self_check_reasons_count",
    }
    assert inputs.get("planner_path_used") is True
    assert inputs.get("self_check_status") == "pass"
    assert inputs.get("self_check_policy_mode") == "warning_only"
    assert inputs.get("self_check_reasons_count") == 0

    thresholds = dict(verify.get("thresholds") or {})
    assert set(thresholds.keys()) == {
        "required_self_check_status",
        "required_self_check_policy_mode",
        "self_check_reasons_count_max",
    }
    assert thresholds.get("required_self_check_status") == "pass"
    assert thresholds.get("required_self_check_policy_mode") == "warning_only"
    assert thresholds.get("self_check_reasons_count_max") == 0


@pytest.mark.asyncio
async def test_verify_contract_warns_on_fallback_with_self_check_issues():
    eng = ReasoningEngine(retriever=_FallbackRetriever(), llm=_FailingLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    verify = dict(diag.get("verify") or {})
    assert verify.get("status") == "warn"
    assert verify.get("reasons") == [
        "self_check_status!=pass",
        "self_check_reasons_count>0",
    ]

    inputs = dict(verify.get("inputs") or {})
    assert inputs.get("planner_path_used") is False
    assert inputs.get("self_check_status") == "warn"
    assert inputs.get("self_check_policy_mode") == "warning_only"
    assert inputs.get("self_check_reasons_count") == 2

    warnings = list(getattr(resp, "warnings", []) or [])
    assert "verify_warning" in warnings
