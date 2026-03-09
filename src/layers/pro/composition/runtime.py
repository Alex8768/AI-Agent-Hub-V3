from __future__ import annotations

from collections import defaultdict
from typing import Protocol, TypedDict

from src.layers.pro.composition.composer import (
    ComposedAgentEdge,
    ComposedAgentGraphSpec,
    ComposedAgentNode,
    validate_composed_agent_graph_spec,
)
from src.layers.pro.composition.registry import AgentRegistry


class CompositionNodeExecutionResult(TypedDict):
    node_id: str
    agent_id: str
    status: str
    input_keys: list[str]
    output_keys: list[str]
    output_payload: dict[str, object]
    error_message: str


class CompositionRuntimeResult(TypedDict):
    graph_id: str
    status: str
    execution_order: list[str]
    node_results: list[CompositionNodeExecutionResult]
    final_output: dict[str, object]
    reason_codes: list[str]
    warnings: list[str]


class CompositionPlanResult(TypedDict):
    execution_order: list[str]
    has_cycle: bool


class CompositionNodeExecutor(Protocol):
    def execute(
        self,
        *,
        node: ComposedAgentNode,
        inputs: dict[str, object],
    ) -> dict[str, object]:
        """Execute one composition node and return normalized payload."""


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_payload(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _build_plan(spec: ComposedAgentGraphSpec) -> CompositionPlanResult:
    nodes = list(spec.get("nodes", []))
    node_ids = [str(row.get("node_id", "") or "") for row in nodes]
    indegree: dict[str, int] = {node_id: 0 for node_id in node_ids}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in list(spec.get("edges", [])):
        from_node_id = str(edge.get("from_node_id", "") or "")
        to_node_id = str(edge.get("to_node_id", "") or "")
        if from_node_id in indegree and to_node_id in indegree:
            adjacency[from_node_id].append(to_node_id)
            indegree[to_node_id] += 1

    ready = sorted([node_id for node_id, count in indegree.items() if count == 0])
    execution_order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        execution_order.append(node_id)
        for to_node_id in sorted(adjacency.get(node_id, [])):
            indegree[to_node_id] = max(0, int(indegree.get(to_node_id, 0)) - 1)
            if indegree[to_node_id] == 0 and to_node_id not in execution_order and to_node_id not in ready:
                ready.append(to_node_id)
                ready.sort()

    return {
        "execution_order": execution_order,
        "has_cycle": len(execution_order) != len(node_ids),
    }


def _collect_node_inputs(
    *,
    node_id: str,
    edges: list[ComposedAgentEdge],
    outputs_by_node: dict[str, dict[str, object]],
    initial_payload: dict[str, object],
    entry_node_id: str,
) -> dict[str, object]:
    merged: dict[str, object] = {}
    if node_id == entry_node_id:
        merged.update(dict(sorted(initial_payload.items(), key=lambda x: x[0])))

    incoming = [edge for edge in edges if str(edge.get("to_node_id", "") or "") == node_id]
    incoming.sort(key=lambda x: str(x.get("from_node_id", "") or ""))
    for edge in incoming:
        from_node_id = str(edge.get("from_node_id", "") or "")
        from_payload = _normalize_payload(outputs_by_node.get(from_node_id, {}))
        required_inputs = list(edge.get("required_inputs", []))
        if required_inputs:
            for key in sorted(required_inputs):
                if key in from_payload:
                    merged[key] = from_payload[key]
        else:
            for key, value in sorted(from_payload.items(), key=lambda x: str(x[0])):
                merged[str(key)] = value
    return merged


def run_composed_agent_graph(
    *,
    spec: ComposedAgentGraphSpec,
    registry: AgentRegistry | None = None,
    executor: CompositionNodeExecutor | None = None,
    initial_payload: object = None,
) -> CompositionRuntimeResult:
    graph_id = _normalize_string(spec.get("graph_id", ""))
    validation = validate_composed_agent_graph_spec(spec=spec, registry=registry)
    if not validation["valid"]:
        return {
            "graph_id": graph_id,
            "status": "rejected",
            "execution_order": [],
            "node_results": [],
            "final_output": {},
            "reason_codes": ["validation_failed"],
            "warnings": [
                row.get("code", "")
                for row in sorted(
                    validation.get("issues", []),
                    key=lambda x: (
                        str(x.get("code", "")),
                        str(x.get("node_id", "")),
                        str(x.get("edge_key", "")),
                    ),
                )
                if str(row.get("code", "")).strip()
            ],
        }

    plan = _build_plan(spec)
    execution_order = list(plan.get("execution_order", []))
    if plan["has_cycle"]:
        return {
            "graph_id": graph_id,
            "status": "failed",
            "execution_order": execution_order,
            "node_results": [],
            "final_output": {},
            "reason_codes": ["cycle_detected"],
            "warnings": [],
        }

    nodes = {str(row.get("node_id", "") or ""): row for row in list(spec.get("nodes", []))}
    edges = list(spec.get("edges", []))
    outputs_by_node: dict[str, dict[str, object]] = {}
    node_results: list[CompositionNodeExecutionResult] = []
    normalized_initial_payload = _normalize_payload(initial_payload)
    entry_node_id = str(spec.get("entry_node_id", "") or "")

    for node_id in execution_order:
        node = dict(nodes.get(node_id, {}))
        agent_id = _normalize_string(node.get("agent_id", ""))
        inputs = _collect_node_inputs(
            node_id=node_id,
            edges=edges,
            outputs_by_node=outputs_by_node,
            initial_payload=normalized_initial_payload,
            entry_node_id=entry_node_id,
        )
        if executor is None:
            output_payload: dict[str, object] = {"node_id": node_id}
        else:
            try:
                output_payload = _normalize_payload(executor.execute(node=node, inputs=inputs))
            except Exception as exc:
                return {
                    "graph_id": graph_id,
                    "status": "failed",
                    "execution_order": execution_order,
                    "node_results": node_results
                    + [
                        {
                            "node_id": node_id,
                            "agent_id": agent_id,
                            "status": "failed",
                            "input_keys": sorted(inputs.keys()),
                            "output_keys": [],
                            "output_payload": {},
                            "error_message": _normalize_string(exc),
                        }
                    ],
                    "final_output": {},
                    "reason_codes": ["node_execution_failed"],
                    "warnings": [node_id],
                }

        outputs_by_node[node_id] = output_payload
        node_results.append(
            {
                "node_id": node_id,
                "agent_id": agent_id,
                "status": "succeeded",
                "input_keys": sorted(inputs.keys()),
                "output_keys": sorted([str(key) for key in output_payload.keys()]),
                "output_payload": output_payload,
                "error_message": "",
            }
        )

    exit_node_id = str(spec.get("exit_node_id", "") or "")
    return {
        "graph_id": graph_id,
        "status": "succeeded",
        "execution_order": execution_order,
        "node_results": node_results,
        "final_output": _normalize_payload(outputs_by_node.get(exit_node_id, {})),
        "reason_codes": [],
        "warnings": [],
    }
