from __future__ import annotations

from src.layers.pro.composition.composer import (
    build_composed_agent_graph_spec,
    validate_composed_agent_graph_spec,
)
from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.reasoning.planner.composition_boundary import (
    CompositionRequest,
    CompositionResolution,
    build_composition_resolution,
)


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


def resolve_composition_request(*, request: CompositionRequest) -> CompositionResolution:
    query = str(request.get("query", "") or "").strip()
    composition_mode = bool(request.get("composition_mode", False))
    registry = request.get("composition_registry")
    if not composition_mode:
        return build_composition_resolution(
            mode="disabled",
            reason_codes=["composition_mode_disabled"],
            diagnostics={"query_present": bool(query), "registry_present": bool(registry is not None)},
        )
    if not query:
        return build_composition_resolution(
            mode="fallback",
            reason_codes=["empty_query"],
            diagnostics={"query_present": False, "registry_present": bool(registry is not None)},
            step_descriptions=[],
            composition_graph=None,
        )
    graph_spec = _build_composition_graph(query=query, registry=registry if isinstance(registry, AgentRegistry) else None)
    if graph_spec is None:
        return build_composition_resolution(
            mode="fallback",
            reason_codes=["composition_graph_unavailable"],
            diagnostics={"query_present": True, "registry_present": bool(registry is not None)},
            step_descriptions=[f"Answer query using verified evidence: {query}"],
            composition_graph=None,
        )
    return build_composition_resolution(
        mode="resolved",
        reason_codes=[],
        diagnostics={"query_present": True, "registry_present": bool(registry is not None)},
        step_descriptions=[f"Compose plan and execute graph for query: {query}"],
        composition_graph=graph_spec,
    )

