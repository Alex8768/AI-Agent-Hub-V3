from __future__ import annotations

from typing import TypedDict


class PlanStep(TypedDict):
    description: str


class ReasoningPlan(TypedDict):
    steps: list[PlanStep]


def build_reasoning_plan(*, step_descriptions: list[str]) -> ReasoningPlan:
    """Build normalized reasoning plan from textual step descriptions."""
    steps: list[PlanStep] = []
    for raw in step_descriptions:
        description = str(raw or "").strip()
        if not description:
            continue
        steps.append({"description": description})
    return {"steps": steps}
