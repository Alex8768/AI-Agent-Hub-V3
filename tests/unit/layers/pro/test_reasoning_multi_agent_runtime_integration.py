from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _EmptyRetriever:
    async def retrieve(self, request):
        _ = request
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


@pytest.mark.asyncio
async def test_execute_planner_steps_enriches_multi_agent_runtime_contract(monkeypatch):
    def _fake_create_reasoning_plan(*, query: str):
        _ = query
        return {
            "steps": [
                {"description": "collect"},
                {"description": "critique"},
                {"description": "answer"},
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
                "step_description": "critique",
                "reasoning_output": "critique",
                "verify_status": "warn",
                "verify_reasons": ["low_coverage"],
            },
            {
                "step_index": 2,
                "step_description": "answer",
                "reasoning_output": "answer",
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

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))

    assert [str((x or {}).get("agent_role", "")) for x in rows] == [
        "researcher",
        "critic",
        "synthesizer",
    ]
    handoffs = list((rows[1] or {}).get("handoff_transitions") or [])
    assert handoffs == [
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

    selected = [bool((x or {}).get("selected_by_arbitration")) for x in rows]
    assert selected == [False, False, True]
    decision = dict((rows[2] or {}).get("arbitration_decision") or {})
    assert decision.get("winner_role") == "synthesizer"
    assert decision.get("strategy") == "highest_score"


@pytest.mark.asyncio
async def test_execute_planner_steps_handles_empty_plan_with_multi_agent_runtime(monkeypatch):
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.create_reasoning_plan",
        lambda *, query: {"steps": []},
    )

    async def _fake_execute_plan_steps(*, plan, run_reasoning_step, run_verify_step, max_steps=None):
        _ = plan
        _ = run_reasoning_step
        _ = run_verify_step
        _ = max_steps
        return []

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.execute_plan_steps",
        _fake_execute_plan_steps,
    )

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))
    assert rows == []


@pytest.mark.asyncio
async def test_execute_planner_steps_applies_tool_safety_runtime_guard(monkeypatch):
    def _fake_create_reasoning_plan(*, query: str):
        _ = query
        return {"steps": [{"description": "run shell command"}]}

    async def _fake_execute_plan_steps(*, plan, run_reasoning_step, run_verify_step, max_steps=None):
        _ = plan
        _ = run_reasoning_step
        _ = run_verify_step
        _ = max_steps
        return [
            {
                "step_index": 0,
                "step_description": "run shell command",
                "reasoning_output": "ok",
                "verify_status": "pass",
                "verify_reasons": [],
            }
        ]

    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.create_reasoning_plan",
        _fake_create_reasoning_plan,
    )
    monkeypatch.setattr(
        "src.layers.pro.reasoning.engine.execute_plan_steps",
        _fake_execute_plan_steps,
    )

    eng = ReasoningEngine(retriever=_EmptyRetriever())
    rows = await eng._execute_planner_steps_mvp(request=AnswerRequest(query="q"))
    row = dict(rows[0] or {})

    assert row.get("tool_safety_blocked") is True
    decision = dict(row.get("tool_safety_decision") or {})
    assert decision.get("tool_name") == "shell"
    assert decision.get("allowed") is False
    assert decision.get("reason") == "tool_explicitly_denied"
    assert row.get("verify_status") == "warn"
    assert "tool_safety:tool_explicitly_denied" in list(row.get("verify_reasons") or [])
