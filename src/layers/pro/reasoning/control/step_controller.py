from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.control.execution_policy import ReasoningExecutionPolicy
from src.layers.pro.reasoning.planner.plan_model import ReasoningPlan


class ControlledPlanStep(TypedDict):
    step_index: int
    description: str
    retry_budget: int


def build_controlled_plan_steps(
    *,
    plan: ReasoningPlan,
    policy: ReasoningExecutionPolicy,
) -> list[ControlledPlanStep]:
    """Build bounded, normalized plan steps according to execution policy."""
    steps = list(plan.get("steps") or [])
    max_steps = max(0, int(policy.get("max_steps", 0) or 0))
    retry_budget = max(0, int(policy.get("max_retries", 0) or 0))

    bounded = steps[:max_steps]
    controlled: list[ControlledPlanStep] = []
    for idx, raw in enumerate(bounded):
        description = str((raw or {}).get("description", "") or "").strip()
        if not description:
            continue
        controlled.append(
            {
                "step_index": int(idx),
                "description": description,
                "retry_budget": int(retry_budget),
            }
        )
    return controlled
