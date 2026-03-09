from __future__ import annotations

from typing import TypedDict

from src.layers.pro.composition.registry import AgentRegistry


class ComposedAgentNode(TypedDict):
    node_id: str
    agent_id: str
    role: str


class ComposedAgentEdge(TypedDict):
    from_node_id: str
    to_node_id: str
    provided_outputs: list[str]
    required_inputs: list[str]


class ComposedAgentGraphSpec(TypedDict):
    graph_id: str
    nodes: list[ComposedAgentNode]
    edges: list[ComposedAgentEdge]
    entry_node_id: str
    exit_node_id: str
    metadata: dict[str, object]


class CompositionCompatibilityIssue(TypedDict):
    code: str
    message: str
    node_id: str
    edge_key: str


class CompositionValidationResult(TypedDict):
    valid: bool
    issues: list[CompositionCompatibilityIssue]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            rows.append(item)
    return sorted(set(rows))


def build_composed_agent_node(
    *,
    node_id: object,
    agent_id: object,
    role: object = "",
) -> ComposedAgentNode:
    return {
        "node_id": _normalize_string(node_id),
        "agent_id": _normalize_string(agent_id),
        "role": _normalize_string(role),
    }


def build_composed_agent_edge(
    *,
    from_node_id: object,
    to_node_id: object,
    provided_outputs: object = None,
    required_inputs: object = None,
) -> ComposedAgentEdge:
    return {
        "from_node_id": _normalize_string(from_node_id),
        "to_node_id": _normalize_string(to_node_id),
        "provided_outputs": _normalize_string_list(provided_outputs),
        "required_inputs": _normalize_string_list(required_inputs),
    }


def build_composed_agent_graph_spec(
    *,
    graph_id: object,
    nodes: object,
    edges: object,
    entry_node_id: object,
    exit_node_id: object,
    metadata: object = None,
) -> ComposedAgentGraphSpec:
    normalized_nodes: list[ComposedAgentNode] = []
    for raw in list(nodes or []):
        row = dict(raw or {})
        normalized_nodes.append(
            build_composed_agent_node(
                node_id=row.get("node_id", ""),
                agent_id=row.get("agent_id", ""),
                role=row.get("role", ""),
            )
        )
    normalized_nodes.sort(key=lambda x: str(x.get("node_id", "")))

    normalized_edges: list[ComposedAgentEdge] = []
    for raw in list(edges or []):
        row = dict(raw or {})
        normalized_edges.append(
            build_composed_agent_edge(
                from_node_id=row.get("from_node_id", ""),
                to_node_id=row.get("to_node_id", ""),
                provided_outputs=row.get("provided_outputs", []),
                required_inputs=row.get("required_inputs", []),
            )
        )
    normalized_edges.sort(
        key=lambda x: (
            str(x.get("from_node_id", "")),
            str(x.get("to_node_id", "")),
        )
    )
    return {
        "graph_id": _normalize_string(graph_id),
        "nodes": normalized_nodes,
        "edges": normalized_edges,
        "entry_node_id": _normalize_string(entry_node_id),
        "exit_node_id": _normalize_string(exit_node_id),
        "metadata": dict(metadata) if isinstance(metadata, dict) else {},
    }


def validate_composed_agent_graph_spec(
    *,
    spec: ComposedAgentGraphSpec,
    registry: AgentRegistry | None = None,
) -> CompositionValidationResult:
    normalized = build_composed_agent_graph_spec(
        graph_id=spec.get("graph_id", ""),
        nodes=spec.get("nodes", []),
        edges=spec.get("edges", []),
        entry_node_id=spec.get("entry_node_id", ""),
        exit_node_id=spec.get("exit_node_id", ""),
        metadata=spec.get("metadata", {}),
    )
    issues: list[CompositionCompatibilityIssue] = []
    nodes = list(normalized.get("nodes") or [])
    node_ids = [str(row.get("node_id", "") or "") for row in nodes]
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        issues.append(
            {
                "code": "duplicate_node_id",
                "message": "Duplicate node_id found in graph spec",
                "node_id": "",
                "edge_key": "",
            }
        )
    for row in nodes:
        node_id = str(row.get("node_id", "") or "")
        agent_id = str(row.get("agent_id", "") or "")
        if not node_id:
            issues.append(
                {
                    "code": "missing_node_id",
                    "message": "Node must include non-empty node_id",
                    "node_id": "",
                    "edge_key": "",
                }
            )
        if not agent_id:
            issues.append(
                {
                    "code": "missing_agent_id",
                    "message": "Node must include non-empty agent_id",
                    "node_id": node_id,
                    "edge_key": "",
                }
            )
            continue
        if registry is not None:
            agent = registry.get(agent_id)
            if not agent:
                issues.append(
                    {
                        "code": "unknown_agent",
                        "message": f"Agent '{agent_id}' is not registered",
                        "node_id": node_id,
                        "edge_key": "",
                    }
                )
            elif not bool(agent.get("enabled", False)):
                issues.append(
                    {
                        "code": "agent_disabled",
                        "message": f"Agent '{agent_id}' is disabled",
                        "node_id": node_id,
                        "edge_key": "",
                    }
                )

    for edge in list(normalized.get("edges") or []):
        from_node_id = str(edge.get("from_node_id", "") or "")
        to_node_id = str(edge.get("to_node_id", "") or "")
        edge_key = f"{from_node_id}->{to_node_id}"
        if from_node_id not in node_id_set or to_node_id not in node_id_set:
            issues.append(
                {
                    "code": "edge_unknown_node",
                    "message": "Edge references unknown node",
                    "node_id": "",
                    "edge_key": edge_key,
                }
            )
            continue
        if from_node_id == to_node_id:
            issues.append(
                {
                    "code": "self_loop_edge",
                    "message": "Edge cannot reference same from/to node",
                    "node_id": from_node_id,
                    "edge_key": edge_key,
                }
            )

        provided_outputs = set(_normalize_string_list(edge.get("provided_outputs", [])))
        required_inputs = set(_normalize_string_list(edge.get("required_inputs", [])))
        if required_inputs and provided_outputs and not required_inputs.issubset(provided_outputs):
            issues.append(
                {
                    "code": "edge_mapping_mismatch",
                    "message": "required_inputs must be subset of provided_outputs",
                    "node_id": to_node_id,
                    "edge_key": edge_key,
                }
            )

        if registry is not None:
            from_node = next((x for x in nodes if x.get("node_id") == from_node_id), {})
            to_node = next((x for x in nodes if x.get("node_id") == to_node_id), {})
            from_agent = registry.get(str(from_node.get("agent_id", "") or ""))
            to_agent = registry.get(str(to_node.get("agent_id", "") or ""))
            from_props = set(
                dict(dict(from_agent or {}).get("output_schema", {}) or {}).get("properties", {}).keys()
            )
            to_props = set(
                dict(dict(to_agent or {}).get("input_schema", {}) or {}).get("properties", {}).keys()
            )
            if provided_outputs and from_props and not provided_outputs.issubset(from_props):
                issues.append(
                    {
                        "code": "edge_output_schema_incompatible",
                        "message": "provided_outputs are not supported by from-node output schema",
                        "node_id": from_node_id,
                        "edge_key": edge_key,
                    }
                )
            if required_inputs and to_props and not required_inputs.issubset(to_props):
                issues.append(
                    {
                        "code": "edge_input_schema_incompatible",
                        "message": "required_inputs are not supported by to-node input schema",
                        "node_id": to_node_id,
                        "edge_key": edge_key,
                    }
                )

    entry = str(normalized.get("entry_node_id", "") or "")
    exit_node = str(normalized.get("exit_node_id", "") or "")
    if entry and entry not in node_id_set:
        issues.append(
            {
                "code": "unknown_entry_node",
                "message": "entry_node_id is not found in nodes",
                "node_id": entry,
                "edge_key": "",
            }
        )
    if exit_node and exit_node not in node_id_set:
        issues.append(
            {
                "code": "unknown_exit_node",
                "message": "exit_node_id is not found in nodes",
                "node_id": exit_node,
                "edge_key": "",
            }
        )

    issues.sort(
        key=lambda x: (
            str(x.get("code", "")),
            str(x.get("node_id", "")),
            str(x.get("edge_key", "")),
        )
    )
    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }
