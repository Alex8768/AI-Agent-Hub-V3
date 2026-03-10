from __future__ import annotations

import re

from src.layers.pro.composition.composer import build_composed_agent_graph_spec, validate_composed_agent_graph_spec
from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.kernel import normalize_reasoning_query_input
from src.layers.pro.reasoning.planner.plan_model import (
    ReasoningPlan,
    build_reasoning_composition_plan,
    build_reasoning_plan,
)


_SPLIT_HINT_RE = re.compile(r"\b(and|then|after|before)\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"\?$")


def _build_composition_graph(*, query: str, registry: AgentRegistry | None) -> dict[str, object] | None:
    if registry is None:
        return None
    planner_candidates = registry.find_by_capabilities(["plan"])
    executor_candidates = registry.find_by_capabilities(["execute"])
    if not planner_candidates or not executor_candidates:
        return None
    planner_agent_id = str(planner_candidates[0].get("agent_id", "") or "")
    executor_agent_id = str(executor_candidates[0].get("agent_id", "") or "")
    if not planner_agent_id or not executor_agent_id:
        return None
    normalized_query = str(query or "").strip()
    graph_spec = build_composed_agent_graph_spec(
        graph_id=f"composition:{normalized_query.lower().replace(' ', '_') or 'query'}",
        nodes=[
            {"node_id": "plan", "agent_id": planner_agent_id, "role": "plan"},
            {"node_id": "exec", "agent_id": executor_agent_id, "role": "execute"},
        ],
        edges=[
            {
                "from_node_id": "plan",
                "to_node_id": "exec",
                "provided_outputs": ["plan"],
                "required_inputs": ["plan"],
            }
        ],
        entry_node_id="plan",
        exit_node_id="exec",
        metadata={"source": "reasoning_planner", "query": normalized_query},
    )
    validation = validate_composed_agent_graph_spec(spec=graph_spec, registry=registry)
    if not validation["valid"]:
        return None
    return graph_spec


def create_reasoning_plan(
    *,
    query: str | AnswerRequest,
    composition_mode: bool = False,
    composition_registry: AgentRegistry | None = None,
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
            return build_reasoning_composition_plan(
                step_descriptions=[],
                composition_graph=None,
                reason_codes=["empty_query"],
            )
        return {"steps": []}

    base = _QUESTION_RE.sub("", normalized).strip()
    if not base:
        if composition_mode:
            return build_reasoning_composition_plan(
                step_descriptions=[],
                composition_graph=None,
                reason_codes=["empty_query"],
            )
        return {"steps": []}

    if composition_mode:
        graph_spec = _build_composition_graph(query=base, registry=composition_registry)
        if graph_spec is None:
            return build_reasoning_composition_plan(
                step_descriptions=[
                    f"Answer query using verified evidence: {base}",
                ],
                composition_graph=None,
                reason_codes=["composition_graph_unavailable"],
            )
        return build_reasoning_composition_plan(
            step_descriptions=[
                f"Compose plan and execute graph for query: {base}",
            ],
            composition_graph=graph_spec,
            reason_codes=[],
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
