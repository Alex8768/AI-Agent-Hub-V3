from __future__ import annotations

from src.layers.pro.composition.composer import (
    build_composed_agent_graph_spec,
    validate_composed_agent_graph_spec,
)
from src.layers.pro.composition.registry import AgentRegistry


def _build_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        {
            "agent_id": "planner",
            "display_name": "Planner",
            "capabilities": ["plan"],
            "input_schema": {"properties": {"query": {"type": "string"}}},
            "output_schema": {"properties": {"plan": {"type": "string"}}},
            "enabled": True,
            "version": "v1",
        }
    )
    registry.register(
        {
            "agent_id": "executor",
            "display_name": "Executor",
            "capabilities": ["execute"],
            "input_schema": {"properties": {"plan": {"type": "string"}}},
            "output_schema": {"properties": {"answer": {"type": "string"}}},
            "enabled": True,
            "version": "v1",
        }
    )
    return registry


def test_build_graph_spec_normalizes_and_sorts_nodes_edges() -> None:
    spec = build_composed_agent_graph_spec(
        graph_id="  graph-1 ",
        nodes=[
            {"node_id": "n2", "agent_id": "executor", "role": "run"},
            {"node_id": "n1", "agent_id": "planner", "role": "plan"},
        ],
        edges=[
            {
                "from_node_id": "n2",
                "to_node_id": "n1",
                "provided_outputs": ["answer", "answer"],
                "required_inputs": ["query"],
            },
            {
                "from_node_id": "n1",
                "to_node_id": "n2",
                "provided_outputs": ["plan"],
                "required_inputs": ["plan"],
            },
        ],
        entry_node_id=" n1 ",
        exit_node_id=" n2 ",
        metadata={"mode": "mvp"},
    )
    assert spec["graph_id"] == "graph-1"
    assert [x["node_id"] for x in spec["nodes"]] == ["n1", "n2"]
    assert [f"{x['from_node_id']}->{x['to_node_id']}" for x in spec["edges"]] == ["n1->n2", "n2->n1"]
    assert spec["entry_node_id"] == "n1"
    assert spec["exit_node_id"] == "n2"


def test_validate_graph_spec_passes_when_mappings_and_schemas_match() -> None:
    registry = _build_registry()
    spec = build_composed_agent_graph_spec(
        graph_id="graph-ok",
        nodes=[
            {"node_id": "plan", "agent_id": "planner"},
            {"node_id": "exec", "agent_id": "executor"},
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
    )
    result = validate_composed_agent_graph_spec(spec=spec, registry=registry)
    assert result["valid"] is True
    assert result["issues"] == []


def test_validate_graph_spec_reports_deterministic_compatibility_issues() -> None:
    registry = _build_registry()
    spec = build_composed_agent_graph_spec(
        graph_id="graph-bad",
        nodes=[
            {"node_id": "plan", "agent_id": "planner"},
            {"node_id": "exec", "agent_id": "executor"},
        ],
        edges=[
            {
                "from_node_id": "plan",
                "to_node_id": "exec",
                "provided_outputs": ["unknown_output"],
                "required_inputs": ["plan"],
            },
            {
                "from_node_id": "exec",
                "to_node_id": "missing",
                "provided_outputs": ["answer"],
                "required_inputs": ["query"],
            },
        ],
        entry_node_id="unknown",
        exit_node_id="exec",
    )
    result = validate_composed_agent_graph_spec(spec=spec, registry=registry)
    codes = [row["code"] for row in result["issues"]]
    assert result["valid"] is False
    assert "edge_output_schema_incompatible" in codes
    assert "edge_mapping_mismatch" in codes
    assert "edge_unknown_node" in codes
    assert "unknown_entry_node" in codes
