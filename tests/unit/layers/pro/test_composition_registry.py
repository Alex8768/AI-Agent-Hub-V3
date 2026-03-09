from __future__ import annotations

import pytest

from src.layers.pro.composition.registry import (
    AgentRegistry,
    build_registered_agent_spec,
)


def test_build_registered_agent_spec_normalizes_values():
    spec = build_registered_agent_spec(
        agent_id=" agent.search ",
        display_name=" Search Agent ",
        capabilities=["Search", " search ", "read"],
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"answer": {"type": "string"}}},
        enabled=1,
        version=" v2 ",
    )
    assert spec == {
        "agent_id": "agent.search",
        "display_name": "Search Agent",
        "capabilities": ["read", "search"],
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
        "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
        "enabled": True,
        "version": "v2",
    }


def test_agent_registry_register_get_and_list_are_deterministic():
    reg = AgentRegistry()
    reg.register(
        {
            "agent_id": "agent.b",
            "display_name": "Agent B",
            "capabilities": ["search"],
            "enabled": True,
        }
    )
    reg.register(
        {
            "agent_id": "agent.a",
            "display_name": "Agent A",
            "capabilities": ["search", "summarize"],
            "enabled": False,
        }
    )
    assert reg.get("agent.b") == {
        "agent_id": "agent.b",
        "display_name": "Agent B",
        "capabilities": ["search"],
        "input_schema": {},
        "output_schema": {},
        "enabled": True,
        "version": "v1",
    }
    assert [row["agent_id"] for row in reg.list()] == ["agent.a", "agent.b"]
    assert [row["agent_id"] for row in reg.list(enabled_only=True)] == ["agent.b"]


def test_agent_registry_find_by_capabilities_filters_enabled_agents():
    reg = AgentRegistry()
    reg.register(
        {
            "agent_id": "agent.search",
            "display_name": "Search Agent",
            "capabilities": ["search", "read"],
            "enabled": True,
        }
    )
    reg.register(
        {
            "agent_id": "agent.compose",
            "display_name": "Compose Agent",
            "capabilities": ["search", "summarize", "compose"],
            "enabled": True,
        }
    )
    reg.register(
        {
            "agent_id": "agent.disabled",
            "display_name": "Disabled",
            "capabilities": ["search", "summarize"],
            "enabled": False,
        }
    )
    rows = reg.find_by_capabilities(["search", "summarize"])
    assert [row["agent_id"] for row in rows] == ["agent.compose"]


def test_agent_registry_requires_mandatory_fields():
    reg = AgentRegistry()
    with pytest.raises(ValueError, match="agent_id"):
        reg.register({"display_name": "missing id"})
    with pytest.raises(ValueError, match="display_name"):
        reg.register({"agent_id": "agent.x"})
