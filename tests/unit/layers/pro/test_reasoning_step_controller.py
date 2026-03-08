from __future__ import annotations

from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps


def test_build_controlled_plan_steps_respects_max_steps():
    policy = build_reasoning_execution_policy(max_steps=2, max_retries=1)
    plan = {
        "steps": [
            {"description": "step-1"},
            {"description": "step-2"},
            {"description": "step-3"},
        ]
    }
    controlled = build_controlled_plan_steps(plan=plan, policy=policy)
    assert [s["description"] for s in controlled] == ["step-1", "step-2"]
    assert [s["step_index"] for s in controlled] == [0, 1]


def test_build_controlled_plan_steps_assigns_retry_budget_from_policy():
    policy = build_reasoning_execution_policy(max_steps=3, max_retries=2)
    plan = {"steps": [{"description": "only"}]}
    controlled = build_controlled_plan_steps(plan=plan, policy=policy)
    assert controlled == [{"step_index": 0, "description": "only", "retry_budget": 2}]


def test_build_controlled_plan_steps_skips_blank_descriptions():
    policy = build_reasoning_execution_policy(max_steps=5, max_retries=0)
    plan = {
        "steps": [
            {"description": "  first  "},
            {"description": " "},
            {"description": ""},
            {"description": "second"},
        ]
    }
    controlled = build_controlled_plan_steps(plan=plan, policy=policy)
    assert controlled == [
        {"step_index": 0, "description": "first", "retry_budget": 0},
        {"step_index": 3, "description": "second", "retry_budget": 0},
    ]


def test_build_controlled_plan_steps_handles_empty_plan():
    policy = build_reasoning_execution_policy(max_steps=3, max_retries=1)
    assert build_controlled_plan_steps(plan={"steps": []}, policy=policy) == []
