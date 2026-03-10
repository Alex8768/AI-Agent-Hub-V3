from __future__ import annotations

from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.reasoning.planner.composition_boundary import build_composition_request
from src.layers.pro.reasoning.planner.composition_resolver import resolve_composition_request


def _build_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        {
            "agent_id": "planner-agent",
            "display_name": "Planner Agent",
            "capabilities": ["plan"],
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
            "enabled": True,
        }
    )
    return registry


def test_resolve_composition_request_resolved_mode_with_graph():
    resolution = resolve_composition_request(
        request=build_composition_request(
            query="Summarize launch risks",
            composition_mode=True,
            composition_registry=_build_registry(),
        )
    )
    assert resolution["mode"] == "resolved"
    assert resolution["reason_codes"] == []
    assert "composition_graph" in resolution and resolution["composition_graph"]


def test_resolve_composition_request_fallback_mode_when_graph_unavailable():
    resolution = resolve_composition_request(
        request=build_composition_request(
            query="Summarize launch risks",
            composition_mode=True,
            composition_registry=AgentRegistry(),
        )
    )
    assert resolution["mode"] == "fallback"
    assert resolution["reason_codes"] == ["composition_graph_unavailable"]
    assert resolution["step_descriptions"] == [
        "Answer query using verified evidence: Summarize launch risks"
    ]
