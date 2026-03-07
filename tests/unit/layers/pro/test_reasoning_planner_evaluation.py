from __future__ import annotations

import pytest

from src.layers.pro.reasoning.planner.planner import create_reasoning_plan
from src.layers.pro.reasoning.planner.step_executor import execute_plan_steps


@pytest.mark.asyncio
async def test_planner_evaluation_multi_step_reasoning_correctness():
    query = "Find capital of France and confirm country relation"
    plan = create_reasoning_plan(query=query)
    assert len(plan.get("steps") or []) == 2

    async def _run_reasoning_step(step):
        description = str(step.get("description", "") or "")
        return f"reasoned:{description}"

    async def _run_verify_step(reasoning_output: str):
        assert reasoning_output.startswith("reasoned:")
        return {"status": "pass", "reasons": []}

    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=3,
    )

    assert len(results) == 2
    assert [r["step_index"] for r in results] == [0, 1]
    assert all(r["verify_status"] == "pass" for r in results)
    assert all(r["verify_reasons"] == [] for r in results)


@pytest.mark.asyncio
async def test_planner_evaluation_state_propagation_across_steps():
    query = "Collect fact and then refine conclusion"
    plan = create_reasoning_plan(query=query)
    assert len(plan.get("steps") or []) == 2

    state = {"last_output": "seed"}

    async def _run_reasoning_step(step):
        description = str(step.get("description", "") or "")
        output = f"{state['last_output']} -> {description}"
        state["last_output"] = output
        return output

    async def _run_verify_step(reasoning_output: str):
        return {"status": "pass", "reasons": [reasoning_output]}

    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=3,
    )

    assert len(results) == 2
    first = results[0]["reasoning_output"]
    second = results[1]["reasoning_output"]
    assert first.startswith("seed -> ")
    assert second.startswith(first + " -> ")


@pytest.mark.asyncio
async def test_planner_evaluation_verify_runs_per_step_with_stable_fields():
    query = "Gather evidence and then produce answer"
    plan = create_reasoning_plan(query=query)
    assert len(plan.get("steps") or []) == 2

    verify_calls: list[str] = []

    async def _run_reasoning_step(step):
        description = str(step.get("description", "") or "")
        return f"payload:{description}"

    async def _run_verify_step(reasoning_output: str):
        verify_calls.append(reasoning_output)
        if len(verify_calls) == 1:
            return {"status": "warn", "reasons": ["needs_more_support"]}
        return {"status": "pass", "reasons": []}

    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=3,
    )

    assert len(verify_calls) == 2
    assert verify_calls == [r["reasoning_output"] for r in results]
    assert [r["verify_status"] for r in results] == ["warn", "pass"]
    assert [r["verify_reasons"] for r in results] == [["needs_more_support"], []]


@pytest.mark.asyncio
async def test_planner_evaluation_respects_max_steps_safety_guard():
    plan = {
        "steps": [
            {"description": "step-1"},
            {"description": "step-2"},
            {"description": "step-3"},
            {"description": "step-4"},
        ]
    }
    executed: list[str] = []

    async def _run_reasoning_step(step):
        description = str(step.get("description", "") or "")
        executed.append(description)
        return f"out:{description}"

    async def _run_verify_step(reasoning_output: str):
        return {"status": "pass", "reasons": [reasoning_output]}

    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=2,
    )

    assert executed == ["step-1", "step-2"]
    assert [r["step_index"] for r in results] == [0, 1]
    assert [r["step_description"] for r in results] == ["step-1", "step-2"]
