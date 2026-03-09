from __future__ import annotations

from src.layers.pro.composition.composer import build_composed_agent_graph_spec
from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.composition.runtime import run_composed_agent_graph


class _StaticExecutor:
    def execute(self, *, node: dict[str, object], inputs: dict[str, object]) -> dict[str, object]:
        node_id = str(node.get("node_id", ""))
        if node_id == "plan":
            return {"plan": f"built:{inputs.get('query', '')}"}
        if node_id == "exec":
            return {"answer": f"done:{inputs.get('plan', '')}"}
        return {"node_id": node_id}


def _build_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        {
            "agent_id": "planner",
            "display_name": "Planner",
            "input_schema": {"properties": {"query": {"type": "string"}}},
            "output_schema": {"properties": {"plan": {"type": "string"}}},
            "enabled": True,
        }
    )
    registry.register(
        {
            "agent_id": "executor",
            "display_name": "Executor",
            "input_schema": {"properties": {"plan": {"type": "string"}}},
            "output_schema": {"properties": {"answer": {"type": "string"}}},
            "enabled": True,
        }
    )
    return registry


def test_run_composed_agent_graph_succeeds_with_deterministic_order() -> None:
    spec = build_composed_agent_graph_spec(
        graph_id="graph-ok",
        nodes=[
            {"node_id": "exec", "agent_id": "executor"},
            {"node_id": "plan", "agent_id": "planner"},
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
    result = run_composed_agent_graph(
        spec=spec,
        registry=_build_registry(),
        executor=_StaticExecutor(),
        initial_payload={"query": "hello"},
    )
    assert result["status"] == "succeeded"
    assert result["execution_order"] == ["plan", "exec"]
    assert result["final_output"] == {"answer": "done:built:hello"}


def test_run_composed_agent_graph_rejects_invalid_spec() -> None:
    spec = build_composed_agent_graph_spec(
        graph_id="graph-invalid",
        nodes=[{"node_id": "plan", "agent_id": "planner"}],
        edges=[],
        entry_node_id="missing",
        exit_node_id="plan",
    )
    result = run_composed_agent_graph(spec=spec, registry=_build_registry(), executor=_StaticExecutor())
    assert result["status"] == "rejected"
    assert result["reason_codes"] == ["validation_failed"]
    assert "unknown_entry_node" in result["warnings"]


def test_run_composed_agent_graph_fails_on_cycle() -> None:
    spec = build_composed_agent_graph_spec(
        graph_id="graph-cycle",
        nodes=[
            {"node_id": "a", "agent_id": "planner"},
            {"node_id": "b", "agent_id": "executor"},
        ],
        edges=[
            {"from_node_id": "a", "to_node_id": "b"},
            {"from_node_id": "b", "to_node_id": "a"},
        ],
        entry_node_id="a",
        exit_node_id="b",
    )
    result = run_composed_agent_graph(spec=spec, executor=_StaticExecutor())
    assert result["status"] == "failed"
    assert result["reason_codes"] == ["cycle_detected"]
