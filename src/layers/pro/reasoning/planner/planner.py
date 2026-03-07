from __future__ import annotations

import re

from src.layers.pro.reasoning.planner.plan_model import ReasoningPlan, build_reasoning_plan


_SPLIT_HINT_RE = re.compile(r"\b(and|then|after|before)\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"\?$")


def create_reasoning_plan(*, query: str) -> ReasoningPlan:
    """Create deterministic MVP reasoning plan from a query.

    Rules:
    - empty/blank query -> empty plan
    - query with split hints (and/then/after/before) -> 2-step plan
    - otherwise -> single-step plan
    """
    normalized = str(query or "").strip()
    if not normalized:
        return {"steps": []}

    base = _QUESTION_RE.sub("", normalized).strip()
    if not base:
        return {"steps": []}

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
