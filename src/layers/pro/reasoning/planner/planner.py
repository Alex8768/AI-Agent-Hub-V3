from __future__ import annotations

import re

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.kernel import normalize_reasoning_query_input
from src.layers.pro.reasoning.planner.plan_model import (
    ReasoningPlan,
    build_reasoning_composition_plan,
    build_reasoning_plan,
)
from src.layers.pro.reasoning.planner.composition_boundary import (
    build_composition_request,
)
from src.layers.pro.reasoning.planner.composition_resolver import resolve_composition_request


_SPLIT_HINT_RE = re.compile(r"\b(and|then|after|before)\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"\?$")


def create_reasoning_plan(
    *,
    query: str | AnswerRequest,
    composition_mode: bool = False,
    composition_registry: object | None = None,
) -> ReasoningPlan:
    """Create deterministic MVP reasoning plan from a query.

    Rules:
    - empty/blank query -> empty plan
    - query with split hints (and/then/after/before) -> 2-step plan
    - otherwise -> single-step plan
    """
    normalized = normalize_reasoning_query_input(query)
    if not normalized:
        if composition_mode:
            request = build_composition_request(
                query="",
                composition_mode=True,
                composition_registry=composition_registry,
            )
            resolution = resolve_composition_request(request=request)
            return build_reasoning_composition_plan(
                step_descriptions=list(resolution.get("step_descriptions") or []),
                composition_graph=resolution.get("composition_graph"),
                reason_codes=list(resolution.get("reason_codes") or []),
            )
        return {"steps": []}

    base = _QUESTION_RE.sub("", normalized).strip()
    if not base:
        if composition_mode:
            request = build_composition_request(
                query="",
                composition_mode=True,
                composition_registry=composition_registry,
            )
            resolution = resolve_composition_request(request=request)
            return build_reasoning_composition_plan(
                step_descriptions=list(resolution.get("step_descriptions") or []),
                composition_graph=resolution.get("composition_graph"),
                reason_codes=list(resolution.get("reason_codes") or []),
            )
        return {"steps": []}

    if composition_mode:
        request = build_composition_request(
            query=base,
            composition_mode=True,
            composition_registry=composition_registry,
        )
        resolution = resolve_composition_request(request=request)
        return build_reasoning_composition_plan(
            step_descriptions=list(resolution.get("step_descriptions") or []),
            composition_graph=resolution.get("composition_graph"),
            reason_codes=list(resolution.get("reason_codes") or []),
        )

    if _SPLIT_HINT_RE.search(base):
        return build_reasoning_plan(
            step_descriptions=[
                f"Analyze query intent: {base}",
                f"Synthesize final answer from verified evidence: {base}",
            ]
        )

    return build_reasoning_plan(
        step_descriptions=[
            f"Answer query using verified evidence: {base}",
        ]
    )
