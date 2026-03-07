from __future__ import annotations

from typing import Awaitable, Callable, TypedDict

from src.layers.pro.reasoning.planner.plan_model import PlanStep, ReasoningPlan


class StepExecutionResult(TypedDict):
    step_index: int
    step_description: str
    reasoning_output: str
    verify_status: str
    verify_reasons: list[str]


async def execute_plan_steps(
    *,
    plan: ReasoningPlan,
    run_reasoning_step: Callable[[PlanStep], Awaitable[str]],
    run_verify_step: Callable[[str], Awaitable[dict[str, object]]],
) -> list[StepExecutionResult]:
    """Execute plan steps sequentially and verify each step output."""
    results: list[StepExecutionResult] = []
    for idx, step in enumerate(list(plan.get("steps") or [])):
        description = str(step.get("description", "") or "").strip()
        reasoning_output = str(await run_reasoning_step({"description": description}))
        verify = dict(await run_verify_step(reasoning_output) or {})
        verify_status = str(verify.get("status", "") or "")
        verify_reasons = [str(x) for x in list(verify.get("reasons") or [])]
        results.append(
            {
                "step_index": int(idx),
                "step_description": description,
                "reasoning_output": reasoning_output,
                "verify_status": verify_status,
                "verify_reasons": verify_reasons,
            }
        )
    return results
