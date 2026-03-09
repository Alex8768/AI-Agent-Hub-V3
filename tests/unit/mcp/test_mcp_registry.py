from __future__ import annotations

import pytest

from src.mcp_protocol.registry import (
    MCPToolRegistry,
    build_mcp_server_spec,
    build_mcp_tool_spec,
)


def test_build_mcp_specs_normalize_values() -> None:
    server = build_mcp_server_spec(
        server_name=" fs ",
        transport="SSE",
        endpoint=" /sse ",
        enabled=1,
        tool_names=["read_file", "read_file"],
    )
    assert server == {
        "server_name": "fs",
        "transport": "sse",
        "endpoint": "/sse",
        "enabled": True,
        "tool_names": ["read_file"],
    }
    tool = build_mcp_tool_spec(
        tool_name=" read_file ",
        server_name=" fs ",
        description=" read file ",
        input_schema={"type": "object"},
        tags=["filesystem", "filesystem"],
        enabled=1,
    )
    assert tool == {
        "tool_name": "read_file",
        "server_name": "fs",
        "description": "read file",
        "input_schema": {"type": "object"},
        "tags": ["filesystem"],
        "enabled": True,
    }


def test_registry_register_and_list_are_deterministic() -> None:
    registry = MCPToolRegistry()
    registry.register_server({"server_name": "server-b"})
    registry.register_server({"server_name": "server-a"})
    registry.register_tool({"tool_name": "tool-b", "server_name": "server-a"})
    registry.register_tool({"tool_name": "tool-a", "server_name": "server-a"})
    assert [x["server_name"] for x in registry.list_servers()] == ["server-a", "server-b"]
    assert [x["tool_name"] for x in registry.list_tools()] == ["tool-a", "tool-b"]
    assert [x["tool_name"] for x in registry.list_tools(server_name="server-a")] == ["tool-a", "tool-b"]


def test_registry_validates_required_fields() -> None:
    registry = MCPToolRegistry()
    with pytest.raises(ValueError, match="server_name is required"):
        registry.register_server({"server_name": ""})
    with pytest.raises(ValueError, match="tool_name is required"):
        registry.register_tool({"tool_name": "", "server_name": "x"})
    with pytest.raises(ValueError, match="server_name is not registered"):
        registry.register_tool({"tool_name": "t1", "server_name": "x"})
