from __future__ import annotations

import pytest

from src.layers.pro.reasoning.tool_safety.decision_engine import build_tool_safety_decision
from src.layers.pro.reasoning.tool_safety.mcp_adapter import build_tool_catalog_entry_from_mcp_tool
from src.layers.pro.reasoning.tool_safety.sandbox_policy import build_tool_safety_sandbox_policy
from src.mcp_protocol.mcp_runtime import execute_mcp_tool_with_safety
from src.mcp_protocol.registry import MCPToolRegistry
from src.mcp_protocol.tool_discovery import build_mcp_tool_discovery_payload


def _registry_for_quality_gate() -> MCPToolRegistry:
    registry = MCPToolRegistry()
    registry.register_server({"server_name": "filesystem", "transport": "stdio", "endpoint": "", "enabled": True})
    registry.register_server({"server_name": "network", "transport": "http", "endpoint": "/mcp", "enabled": True})
    registry.register_tool(
        {
            "tool_name": "read_file",
            "server_name": "filesystem",
            "description": "Read file",
            "input_schema": {"type": "object"},
            "tags": ["filesystem"],
            "enabled": True,
        }
    )
    registry.register_tool(
        {
            "tool_name": "fetch_url",
            "server_name": "network",
            "description": "Fetch URL over network",
            "input_schema": {"type": "object"},
            "tags": ["network"],
            "enabled": True,
        }
    )
    return registry


def test_mcp_quality_gate_registry_and_discovery_are_deterministic():
    registry_a = _registry_for_quality_gate()
    registry_b = _registry_for_quality_gate()
    payload_a = build_mcp_tool_discovery_payload(
        tools=registry_a.list_tools(),
        servers=registry_a.list_servers(),
    )
    payload_b = build_mcp_tool_discovery_payload(
        tools=registry_b.list_tools(),
        servers=registry_b.list_servers(),
    )
    assert payload_a == payload_b


@pytest.mark.asyncio
async def test_mcp_quality_gate_runtime_is_deterministic():
    registry = _registry_for_quality_gate()

    def _invoker(*, tool_name: str, arguments: dict[str, object]):
        return {"tool": tool_name, "arguments": dict(arguments)}

    run_a = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="read_file",
        arguments={"path": "a.txt"},
        invoker=_invoker,
    )
    run_b = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="read_file",
        arguments={"path": "a.txt"},
        invoker=_invoker,
    )
    assert run_a == run_b


@pytest.mark.asyncio
async def test_mcp_quality_gate_runtime_decision_matches_decision_engine():
    registry = _registry_for_quality_gate()
    tool = registry.get_tool("fetch_url")
    assert tool is not None

    # Explicit policy keeps this parity test stable and transparent.
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["fetch_url"],
        denied_tools=["shell"],
        allow_network=False,
    )
    catalog_entry = build_tool_catalog_entry_from_mcp_tool(mcp_tool=tool)
    expected = build_tool_safety_decision(
        tool_name="fetch_url",
        policy=policy,
        catalog=[catalog_entry],
    )
    runtime = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="fetch_url",
        arguments={"url": "https://example.com"},
        invoker=lambda *, tool_name, arguments: {"ok": True, "tool": tool_name, "args": arguments},
        policy=policy,
        catalog=[],
    )
    assert runtime["receipt"]["tool_safety_decision"] == expected
    assert runtime["receipt"]["status"] == "blocked"


@pytest.mark.asyncio
async def test_mcp_quality_gate_fail_safe_for_unknown_tool():
    registry = _registry_for_quality_gate()
    runtime = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="unknown_tool",
        arguments={},
        invoker=lambda *, tool_name, arguments: {"unexpected": True},
    )
    assert runtime["receipt"]["status"] == "blocked"
    assert runtime["receipt"]["reason_codes"] == ["tool_not_registered"]
