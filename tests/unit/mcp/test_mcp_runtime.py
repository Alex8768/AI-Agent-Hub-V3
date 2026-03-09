from __future__ import annotations

import pytest

from src.mcp_protocol.mcp_runtime import execute_mcp_tool_with_safety
from src.mcp_protocol.registry import MCPToolRegistry


def _build_registry(tool_name: str, description: str, tags: list[str]) -> MCPToolRegistry:
    registry = MCPToolRegistry()
    registry.register_server(
        {
            "server_name": "server",
            "transport": "stdio",
            "endpoint": "",
            "enabled": True,
        }
    )
    registry.register_tool(
        {
            "tool_name": tool_name,
            "server_name": "server",
            "description": description,
            "input_schema": {"type": "object"},
            "tags": tags,
            "enabled": True,
        }
    )
    return registry


@pytest.mark.asyncio
async def test_execute_mcp_tool_with_safety_success():
    registry = _build_registry("read_file", "Read file", ["filesystem"])

    async def _invoker(*, tool_name: str, arguments: dict[str, object]):
        return {"tool_name": tool_name, "args": dict(arguments)}

    result = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="read_file",
        arguments={"path": "x.txt"},
        invoker=_invoker,
    )
    assert result["receipt"]["status"] == "succeeded"
    assert result["result"]["tool_name"] == "read_file"


@pytest.mark.asyncio
async def test_execute_mcp_tool_with_safety_blocked_by_policy():
    registry = _build_registry("run_shell", "Execute shell command", ["execution"])

    async def _invoker(*, tool_name: str, arguments: dict[str, object]):
        return {"ok": True}

    result = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="run_shell",
        arguments={"cmd": "ls"},
        invoker=_invoker,
    )
    assert result["receipt"]["status"] == "blocked"
    assert result["receipt"]["allowed"] is False


@pytest.mark.asyncio
async def test_execute_mcp_tool_with_safety_invoker_unavailable():
    registry = _build_registry("read_file", "Read file", ["filesystem"])
    result = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name="read_file",
        arguments={"path": "x.txt"},
        invoker=None,
    )
    assert result["receipt"]["status"] == "failed"
    assert result["error"] == "Invoker unavailable"
