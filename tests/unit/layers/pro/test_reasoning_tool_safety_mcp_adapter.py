from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.mcp_adapter import (
    build_tool_catalog_entry_from_mcp_tool,
    build_tool_catalog_from_mcp_tools,
)


def test_build_tool_catalog_entry_from_mcp_tool_normalizes_and_infers_flags():
    entry = build_tool_catalog_entry_from_mcp_tool(
        mcp_tool={
            "tool_name": " run_shell ",
            "server_name": "local",
            "description": "Execute shell command",
            "input_schema": {},
            "tags": ["execution", "local"],
            "enabled": True,
        }
    )
    assert entry["tool_name"] == "run_shell"
    assert entry["risk_level"] == "high"
    assert "execute" in entry["capabilities"]
    assert entry["requires_execution"] is True


def test_build_tool_catalog_entry_from_mcp_tool_network_inference():
    entry = build_tool_catalog_entry_from_mcp_tool(
        mcp_tool={
            "tool_name": "fetch_url",
            "server_name": "remote",
            "description": "HTTP fetch",
            "input_schema": {},
            "tags": ["network"],
            "enabled": True,
        }
    )
    assert entry["risk_level"] == "medium"
    assert "network" in entry["capabilities"]
    assert entry["requires_network"] is True


def test_build_tool_catalog_from_mcp_tools_is_deterministic():
    rows = [
        {
            "tool_name": "b",
            "server_name": "s",
            "description": "read file",
            "input_schema": {},
            "tags": ["filesystem"],
            "enabled": True,
        },
        {
            "tool_name": "a",
            "server_name": "s",
            "description": "write file",
            "input_schema": {},
            "tags": ["filesystem"],
            "enabled": True,
        },
    ]
    catalog_a = build_tool_catalog_from_mcp_tools(mcp_tools=rows)
    catalog_b = build_tool_catalog_from_mcp_tools(mcp_tools=list(reversed(rows)))
    assert catalog_a == catalog_b
    assert [x["tool_name"] for x in catalog_a] == ["a", "b"]
