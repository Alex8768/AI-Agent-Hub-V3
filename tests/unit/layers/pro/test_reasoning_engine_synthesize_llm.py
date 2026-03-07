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
    assert diag.get("evidence_contract_valid_minimal") is True
    assert diag.get("evidence_contract_missing_minimal_fields") == []
    assert diag.get("evidence_contract_missing_minimal_count") == 0
    assert diag.get("evidence_contract_minimal_coverage_score") == 1.0
    assert diag.get("evidence_contract_gate_reason") == "ok"
    sc = dict(diag.get("self_check") or {})
    assert sc.get("version") == "v1"
    assert sc.get("status") == "pass"
    assert sc.get("reasons") == []
    assert sc.get("policy_mode") == "warning_only"
    sc_inputs = dict(sc.get("inputs") or {})
    assert sc_inputs.get("evidence_contract_valid_minimal") is True
    assert sc_inputs.get("evidence_contract_missing_minimal_count") == 0
    assert sc_inputs.get("evidence_contract_minimal_coverage_score") == 1.0
    sc_thr = dict(sc.get("thresholds") or {})
    assert sc_thr.get("minimal_coverage_score_min") == 1.0
    assert sc_thr.get("missing_minimal_count_max") == 0
    verify = dict(diag.get("verify") or {})
    assert verify.get("version") == "v1"
    assert verify.get("status") == "pass"
    assert verify.get("reasons") == []
    assert verify.get("policy_mode") == "warning_only"
    v_inputs = dict(verify.get("inputs") or {})
    assert v_inputs.get("planner_path_used") is True
    assert v_inputs.get("self_check_status") == "pass"
    assert v_inputs.get("self_check_policy_mode") == "warning_only"
    assert v_inputs.get("self_check_reasons_count") == 0
    v_thr = dict(verify.get("thresholds") or {})
    assert v_thr.get("required_self_check_status") == "pass"
    assert v_thr.get("required_self_check_policy_mode") == "warning_only"
    assert v_thr.get("self_check_reasons_count_max") == 0
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
    assert ec.get("missing_minimal_count") == 0
    assert ec.get("minimal_coverage_score") == 1.0
    assert ec.get("valid_minimal") is True
