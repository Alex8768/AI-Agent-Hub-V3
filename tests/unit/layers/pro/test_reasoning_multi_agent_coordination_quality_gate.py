from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _EmptyRetriever:
    async def retrieve(self, request):
        _ = request
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


def _patch_engine_runtime(monkeypatch):
    def _fake_create_reasoning_plan(*, query: str):
        _ = query
        return {
            "steps": [
                {"description": "collect"},
                {"description": "validate"},
                {"description": "synthesize"},
            ]
        }

    async def _fake_execute_plan_steps(*, plan, run_reasoning_step, run_verify_step, max_steps=None):
        _ = plan
        _ = run_reasoning_step
        _ = run_verify_step
        _ = max_steps
        return [
            {
                "step_index": 0,
                "step_description": "collect",
                "reasoning_output": "collect",
                "verify_status": "pass",
                "verify_reasons": [],
            },
            {
                "step_index": 1,
                "step_description": "validate",
                "reasoning_output": "validate",
                "verify_status": "pass",
                "verify_reasons": [],
            },
            {
                "step_index": 2,
                "step_description": "synthesize",
                "reasoning_output": "synthesize",
                "verify_status": "pass",
                "verify_reasons": [],
            },
        ]

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.create_reasoning_plan",
        _fake_create_reasoning_plan,
    )
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.execute_plan_steps",
        _fake_execute_plan_steps,
    )


@pytest.mark.asyncio
async def test_multi_agent_quality_gate_runtime_is_deterministic(monkeypatch):
    _patch_engine_runtime(monkeypatch)
    eng = ReasoningEngine(retriever=_EmptyRetriever())

    run_a = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))
    run_b = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))
    assert run_a == run_b


@pytest.mark.asyncio
async def test_multi_agent_quality_gate_handoff_order_and_acceptance(monkeypatch):
    _patch_engine_runtime(monkeypatch)
    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))

    assert list((rows[0] or {}).get("handoff_transitions") or []) == []
    assert list((rows[1] or {}).get("handoff_transitions") or []) == [
        {
            "from_step_index": 0,
            "to_step_index": 1,
            "from_role": "researcher",
            "to_role": "critic",
            "output_key": "step_0_output",
            "accepted": True,
            "reason": "handoff_output_key_consumed",
        }
    ]
    assert list((rows[2] or {}).get("handoff_transitions") or []) == [
        {
            "from_step_index": 1,
            "to_step_index": 2,
            "from_role": "critic",
            "to_role": "synthesizer",
            "output_key": "step_1_output",
            "accepted": True,
            "reason": "handoff_output_key_consumed",
        }
    ]
    assert bool((rows[1] or {}).get("handoff_ok")) is True
    assert bool((rows[2] or {}).get("handoff_ok")) is True


@pytest.mark.asyncio
async def test_multi_agent_quality_gate_arbitration_selects_single_winner(monkeypatch):
    _patch_engine_runtime(monkeypatch)
    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))

    selected = [bool((row or {}).get("selected_by_arbitration")) for row in rows]
    assert selected.count(True) == 1
    winner = rows[selected.index(True)]
    decision = dict((winner or {}).get("arbitration_decision") or {})
    assert decision.get("winner_role") == str((winner or {}).get("agent_role", "") or "")
    assert decision.get("strategy") == "highest_score"


@pytest.mark.asyncio
async def test_multi_agent_quality_gate_runtime_contract_parity(monkeypatch):
    _patch_engine_runtime(monkeypatch)
    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))

    expected_step_keys = {
        "step_index",
        "step_description",
        "reasoning_output",
        "verify_status",
        "verify_reasons",
        "agent_role",
        "handoff_transitions",
        "handoff_ok",
        "arbitration_score",
        "selected_by_arbitration",
        "arbitration_decision",
    }
    for row in rows:
        assert set(dict(row or {}).keys()) == expected_step_keys

    decision = dict((rows[-1] or {}).get("arbitration_decision") or {})
    assert set(decision.keys()) == {
        "winner_role",
        "strategy",
        "reasons",
        "confidence_score",
    }
