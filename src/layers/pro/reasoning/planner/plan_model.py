from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TypedDict

if TYPE_CHECKING:
    from src.layers.pro.composition.composer import ComposedAgentGraphSpec


class PlanStep(TypedDict):
    description: str


class ReasoningPlan(TypedDict, total=False):
    steps: list[PlanStep]
    composition_mode: bool
    composition_graph: "ComposedAgentGraphSpec"
    reason_codes: list[str]


def build_reasoning_plan(*, step_descriptions: list[str]) -> ReasoningPlan:
    """Build normalized reasoning plan from textual step descriptions."""
    steps: list[PlanStep] = []
    for raw in step_descriptions:
        description = str(raw or "").strip()
        if not description:
            continue
        steps.append({"description": description})
    return {"steps": steps}


def build_reasoning_composition_plan(
    *,
    step_descriptions: list[str],
    composition_graph: "ComposedAgentGraphSpec" | None,
    reason_codes: list[str] | None = None,
) -> ReasoningPlan:
    plan = build_reasoning_plan(step_descriptions=step_descriptions)
    plan["composition_mode"] = True
    if composition_graph is not None:
        plan["composition_graph"] = composition_graph
    plan["reason_codes"] = sorted(set([str(x or "").strip() for x in list(reason_codes or []) if str(x or "").strip()]))
    return plan
