from __future__ import annotations

from typing import TypedDict

from src.mcp_protocol.registry import MCPServerSpec, MCPToolSpec, build_mcp_server_spec, build_mcp_tool_spec


class MCPToolDiscoveryItem(TypedDict):
    tool_name: str
    server_name: str
    description: str
    input_schema: dict[str, object]
    tags: list[str]
    enabled: bool


class MCPToolDiscoveryPayload(TypedDict):
    tools: list[MCPToolDiscoveryItem]
    servers: list[MCPServerSpec]
    total_tools: int
    total_servers: int


def build_mcp_tool_discovery_item(*, tool: object) -> MCPToolDiscoveryItem:
    row = dict(tool or {})
    normalized = build_mcp_tool_spec(
        tool_name=row.get("tool_name", ""),
        server_name=row.get("server_name", ""),
        description=row.get("description", ""),
        input_schema=row.get("input_schema", {}),
        tags=row.get("tags", []),
        enabled=row.get("enabled", True),
    )
    return dict(normalized)


def build_mcp_tool_discovery_payload(
    *,
    tools: object,
    servers: object,
) -> MCPToolDiscoveryPayload:
    normalized_tools = [build_mcp_tool_discovery_item(tool=x) for x in list(tools or [])]
    normalized_tools.sort(key=lambda x: str(x.get("tool_name", "")))

    normalized_servers: list[MCPServerSpec] = []
    for raw in list(servers or []):
        row = dict(raw or {})
        normalized_servers.append(
            build_mcp_server_spec(
                server_name=row.get("server_name", ""),
                transport=row.get("transport", "stdio"),
                endpoint=row.get("endpoint", ""),
                enabled=row.get("enabled", True),
                tool_names=row.get("tool_names", []),
            )
        )
    normalized_servers.sort(key=lambda x: str(x.get("server_name", "")))
    return {
        "tools": normalized_tools,
        "servers": normalized_servers,
        "total_tools": int(len(normalized_tools)),
        "total_servers": int(len(normalized_servers)),
    }
