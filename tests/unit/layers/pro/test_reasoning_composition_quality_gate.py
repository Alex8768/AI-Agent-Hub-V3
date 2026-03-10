from __future__ import annotations

from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.composition.runtime import run_composed_agent_graph
from src.layers.pro.reasoning.planner.planner import create_reasoning_plan


class _StaticCompositionExecutor:
    def execute(self, *, node: dict[str, object], inputs: dict[str, object]) -> dict[str, object]:
        node_id = str(node.get("node_id", "") or "")
        if node_id == "plan":
            return {"plan": f"p:{inputs.get('query', '')}"}
        if node_id == "exec":
            return {"answer": f"a:{inputs.get('plan', '')}"}
        return {"node_id": node_id}


def _build_composition_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        {
            "agent_id": "planner-agent",
            "display_name": "Planner Agent",
            "capabilities": ["plan"],
            "input_schema": {"properties": {"query": {"type": "string"}}},
            "output_schema": {"properties": {"plan": {"type": "string"}}},
            "enabled": True,
        }
    )
    registry.register(
        {
            "agent_id": "executor-agent",
            "display_name": "Executor Agent",
            "capabilities": ["execute"],
            "input_schema": {"properties": {"plan": {"type": "string"}}},
            "output_schema": {"properties": {"answer": {"type": "string"}}},
            "enabled": True,
        }
    )
    return registry


def test_composition_quality_gate_planner_mode_is_deterministic() -> None:
    registry = _build_composition_registry()
    plan_a = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=registry,
    )
    plan_b = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=registry,
    )
    assert plan_a == plan_b
    assert plan_a.get("composition_mode") is True
    assert "composition_graph" in plan_a


def test_composition_quality_gate_runtime_parity_for_planner_graph() -> None:
    registry = _build_composition_registry()
    plan = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=registry,
    )
    graph = dict(plan.get("composition_graph") or {})
    runtime_a = run_composed_agent_graph(
        spec=graph,
        registry=registry,
        executor=_StaticCompositionExecutor(),
        initial_payload={"query": "Summarize launch risks"},
    )
    runtime_b = run_composed_agent_graph(
        spec=graph,
        registry=registry,
        executor=_StaticCompositionExecutor(),
        initial_payload={"query": "Summarize launch risks"},
    )
    assert runtime_a == runtime_b
    assert runtime_a["status"] == "succeeded"
    assert runtime_a["final_output"] == {"answer": "a:p:Summarize launch risks"}


def test_composition_quality_gate_invalid_graph_is_rejected_safely() -> None:
    runtime = run_composed_agent_graph(
        spec={
            "graph_id": "bad",
            "nodes": [{"node_id": "plan", "agent_id": "planner-agent"}],
            "edges": [],
            "entry_node_id": "missing-node",
            "exit_node_id": "plan",
            "metadata": {},
        },
        registry=_build_composition_registry(),
        executor=_StaticCompositionExecutor(),
        initial_payload={"query": "x"},
    )
    assert runtime["status"] == "rejected"
    assert runtime["reason_codes"] == ["validation_failed"]
    assert "unknown_entry_node" in list(runtime.get("warnings") or [])


def test_composition_quality_gate_fallback_decision_is_deterministic() -> None:
    empty_registry = AgentRegistry()
    plan_a = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=empty_registry,
    )
    plan_b = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=empty_registry,
    )
    assert plan_a == plan_b
    assert plan_a.get("reason_codes") == ["composition_graph_unavailable"]
