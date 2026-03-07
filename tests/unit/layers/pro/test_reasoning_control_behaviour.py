from __future__ import annotations

import pytest

from src.layers.pro.reasoning.control.execution_policy import (
    build_reasoning_execution_policy,
    build_reasoning_execution_policy_from_dict,
)
from src.layers.pro.reasoning.control.loop_guard import (
    apply_reasoning_loop_guard,
    build_reasoning_loop_guard_state,
)
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps
from src.layers.pro.reasoning.planner.step_executor import execute_plan_steps
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry


def _build_bounded_plan_steps(*, plan: dict[str, object], policy: dict[str, int]) -> list[dict[str, str]]:
    controlled = build_controlled_plan_steps(plan=plan, policy=policy)
    loop_guard_state = build_reasoning_loop_guard_state(
        max_visits_per_signature=max(int(policy.get("max_retries", 0)) + 1, 1)
    )
    bounded_steps: list[dict[str, str]] = []
    for row in controlled:
        guard_result = apply_reasoning_loop_guard(
            state=loop_guard_state,
            step_description=row.get("description", ""),
        )
        loop_guard_state = guard_result["state"]
        if bool((guard_result.get("decision") or {}).get("should_stop")):
            break
        bounded_steps.append({"description": str(row.get("description", "") or "")})
    return bounded_steps


@pytest.mark.asyncio
async def test_control_behaviour_enforces_step_budget_and_loop_stop():
    policy = build_reasoning_execution_policy(max_steps=5, max_retries=1)
    plan = {
        "steps": [
            {"description": "repeat"},
            {"description": " repeat "},
            {"description": "REPEAT"},
            {"description": "tail"},
        ]
    }

    bounded_steps = _build_bounded_plan_steps(plan=plan, policy=policy)
    assert bounded_steps == [{"description": "repeat"}, {"description": "repeat"}]

    async def _run_reasoning_step(step):
        return str(step.get("description", "") or "")

    async def _run_verify_step(reasoning_output: str):
        _ = reasoning_output
        return {"status": "pass", "reasons": []}

    results = await execute_plan_steps(
        plan={"steps": bounded_steps},
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=int(policy.get("max_steps", 0) or 0),
    )
    assert [row["step_description"] for row in results] == ["repeat", "repeat"]


@pytest.mark.asyncio
async def test_control_behaviour_is_deterministic_across_identical_runs():
    policy = build_reasoning_execution_policy(max_steps=4, max_retries=1)
    plan = {
        "steps": [
            {"description": "alpha"},
            {"description": "beta"},
            {"description": "beta"},
            {"description": "beta"},
        ]
    }

    async def _run_reasoning_step(step):
        desc = str(step.get("description", "") or "")
        return f"out:{desc}"

    async def _run_verify_step(reasoning_output: str):
        return {"status": "pass", "reasons": [reasoning_output]}

    bounded_a = _build_bounded_plan_steps(plan=plan, policy=policy)
    bounded_b = _build_bounded_plan_steps(plan=plan, policy=policy)
    assert bounded_a == bounded_b

    run_a = await execute_plan_steps(
        plan={"steps": bounded_a},
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=int(policy.get("max_steps", 0) or 0),
    )
    run_b = await execute_plan_steps(
        plan={"steps": bounded_b},
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=int(policy.get("max_steps", 0) or 0),
    )
    assert run_a == run_b


def test_control_behaviour_bounds_quality_retry_by_policy_budget():
    deny_policy = build_reasoning_execution_policy(max_retries=0)
    deny_result = decide_reasoning_quality_retry(
        confidence_score=0.2,
        threshold=0.6,
        attempt=0,
        max_retries=int(deny_policy.get("max_retries", 0) or 0),
    )
    assert deny_result["should_retry"] is False
    assert deny_result["loop_guard_triggered"] is True

    allow_policy = build_reasoning_execution_policy(max_retries=2)
    allow_result = decide_reasoning_quality_retry(
        confidence_score=0.2,
        threshold=0.6,
        attempt=1,
        max_retries=int(allow_policy.get("max_retries", 0) or 0),
    )
    assert allow_result["should_retry"] is True
    assert allow_result["next_attempt"] == 2


def test_control_behaviour_accepts_string_policy_config_inputs():
    policy = build_reasoning_execution_policy_from_dict(
        raw={"max_steps": "2", "max_latency_ms": "9000", "max_retries": "1"}
    )
    plan = {
        "steps": [
            {"description": "s1"},
            {"description": "s2"},
            {"description": "s3"},
        ]
    }
    bounded_steps = _build_bounded_plan_steps(plan=plan, policy=policy)
    assert bounded_steps == [{"description": "s1"}, {"description": "s2"}]
