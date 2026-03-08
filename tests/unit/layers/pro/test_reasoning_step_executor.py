from __future__ import annotations

import pytest

from src.layers.pro.reasoning.planner.step_executor import execute_plan_steps


@pytest.mark.asyncio
async def test_execute_plan_steps_runs_in_order_with_verify_per_step():
    calls: list[str] = []

    async def _run_reasoning(step):
        desc = str(step.get("description", ""))
        calls.append(f"reason:{desc}")
        return f"out:{desc}"

    async def _run_verify(text: str):
        calls.append(f"verify:{text}")
        return {"status": "pass", "reasons": []}

    plan = {
        "steps": [
            {"description": "first step"},
            {"description": "second step"},
        ]
    }
    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning,
        run_verify_step=_run_verify,
    )
    assert calls == [
        "reason:first step",
        "verify:out:first step",
        "reason:second step",
        "verify:out:second step",
    ]
    assert results == [
        {
            "step_index": 0,
            "step_description": "first step",
            "reasoning_output": "out:first step",
            "verify_status": "pass",
            "verify_reasons": [],
        },
        {
            "step_index": 1,
            "step_description": "second step",
            "reasoning_output": "out:second step",
            "verify_status": "pass",
            "verify_reasons": [],
        },
    ]


@pytest.mark.asyncio
async def test_execute_plan_steps_defaults_verify_fields_when_missing():
    async def _run_reasoning(step):
        return "ok"

    async def _run_verify(text: str):
        return {}

    results = await execute_plan_steps(
        plan={"steps": [{"description": "only"}]},
        run_reasoning_step=_run_reasoning,
        run_verify_step=_run_verify,
    )
    assert results[0]["verify_status"] == ""
    assert results[0]["verify_reasons"] == []


@pytest.mark.asyncio
async def test_execute_plan_steps_empty_plan_returns_empty_results():
    async def _run_reasoning(step):
        return "unused"

    async def _run_verify(text: str):
        return {"status": "pass", "reasons": []}

    assert (
        await execute_plan_steps(
            plan={"steps": []},
            run_reasoning_step=_run_reasoning,
            run_verify_step=_run_verify,
        )
        == []
    )


@pytest.mark.asyncio
async def test_execute_plan_steps_respects_max_steps_guard():
    calls: list[str] = []

    async def _run_reasoning(step):
        desc = str(step.get("description", ""))
        calls.append(f"reason:{desc}")
        return desc

    async def _run_verify(text: str):
        calls.append(f"verify:{text}")
        return {"status": "pass", "reasons": []}

    plan = {
        "steps": [
            {"description": "s1"},
            {"description": "s2"},
            {"description": "s3"},
            {"description": "s4"},
        ]
    }
    results = await execute_plan_steps(
        plan=plan,
        run_reasoning_step=_run_reasoning,
        run_verify_step=_run_verify,
        max_steps=2,
    )
    assert [x["step_description"] for x in results] == ["s1", "s2"]
    assert calls == [
        "reason:s1",
        "verify:s1",
        "reason:s2",
        "verify:s2",
    ]
