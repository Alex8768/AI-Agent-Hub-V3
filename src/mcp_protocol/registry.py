from __future__ import annotations

from typing import TypedDict


class MCPToolSpec(TypedDict):
    tool_name: str
    server_name: str
    description: str
    input_schema: dict[str, object]
    tags: list[str]
    enabled: bool


class MCPServerSpec(TypedDict):
    server_name: str
    transport: str
    endpoint: str
    enabled: bool
    tool_names: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            rows.append(item)
    return sorted(set(rows))


def _normalize_schema(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def build_mcp_tool_spec(
    *,
    tool_name: object,
    server_name: object,
    description: object = "",
    input_schema: object = None,
    tags: object = None,
    enabled: object = True,
) -> MCPToolSpec:
    return {
        "tool_name": _normalize_string(tool_name),
        "server_name": _normalize_string(server_name),
        "description": _normalize_string(description),
        "input_schema": _normalize_schema(input_schema),
        "tags": _normalize_string_list(tags),
        "enabled": bool(enabled),
    }


def build_mcp_server_spec(
    *,
    server_name: object,
    transport: object = "stdio",
    endpoint: object = "",
    enabled: object = True,
    tool_names: object = None,
) -> MCPServerSpec:
    normalized_transport = _normalize_string(transport).lower() or "stdio"
    if normalized_transport not in {"stdio", "sse", "http"}:
        normalized_transport = "stdio"
    return {
        "server_name": _normalize_string(server_name),
        "transport": normalized_transport,
        "endpoint": _normalize_string(endpoint),
        "enabled": bool(enabled),
        "tool_names": _normalize_string_list(tool_names),
    }


class MCPToolRegistry:
    """Deterministic in-memory MCP tool registry."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerSpec] = {}
        self._tools: dict[str, MCPToolSpec] = {}

    def register_server(self, spec: dict[str, object] | MCPServerSpec) -> MCPServerSpec:
        row = dict(spec or {})
        normalized = build_mcp_server_spec(
            server_name=row.get("server_name", ""),
            transport=row.get("transport", "stdio"),
            endpoint=row.get("endpoint", ""),
            enabled=row.get("enabled", True),
            tool_names=row.get("tool_names", []),
        )
        if not normalized["server_name"]:
            raise ValueError("server_name is required")
        self._servers[normalized["server_name"]] = normalized
        return dict(normalized)

    def register_tool(self, spec: dict[str, object] | MCPToolSpec) -> MCPToolSpec:
        row = dict(spec or {})
        normalized = build_mcp_tool_spec(
            tool_name=row.get("tool_name", ""),
            server_name=row.get("server_name", ""),
            description=row.get("description", ""),
            input_schema=row.get("input_schema", {}),
            tags=row.get("tags", []),
            enabled=row.get("enabled", True),
        )
        if not normalized["tool_name"]:
            raise ValueError("tool_name is required")
        if not normalized["server_name"]:
            raise ValueError("server_name is required")
        if normalized["server_name"] not in self._servers:
            raise ValueError("server_name is not registered")
        self._tools[normalized["tool_name"]] = normalized
        server = dict(self._servers.get(normalized["server_name"], {}))
        tool_names = _normalize_string_list(list(server.get("tool_names", [])) + [normalized["tool_name"]])
        server["tool_names"] = tool_names
        self._servers[normalized["server_name"]] = build_mcp_server_spec(
            server_name=server.get("server_name", ""),
            transport=server.get("transport", "stdio"),
            endpoint=server.get("endpoint", ""),
            enabled=server.get("enabled", True),
            tool_names=tool_names,
        )
        return dict(normalized)

    def get_server(self, server_name: object) -> MCPServerSpec | None:
        key = _normalize_string(server_name)
        row = self._servers.get(key)
        return dict(row) if row else None

    def get_tool(self, tool_name: object) -> MCPToolSpec | None:
        key = _normalize_string(tool_name)
        row = self._tools.get(key)
        return dict(row) if row else None

    def list_servers(self, *, enabled_only: bool = False) -> list[MCPServerSpec]:
        rows = [dict(x) for x in self._servers.values()]
        if enabled_only:
            rows = [x for x in rows if bool(x.get("enabled", False))]
        rows.sort(key=lambda x: str(x.get("server_name", "")))
        return rows

    def list_tools(self, *, enabled_only: bool = False, server_name: str | None = None) -> list[MCPToolSpec]:
        rows = [dict(x) for x in self._tools.values()]
        if enabled_only:
            rows = [x for x in rows if bool(x.get("enabled", False))]
        if server_name is not None:
            server_key = _normalize_string(server_name)
            rows = [x for x in rows if str(x.get("server_name", "")) == server_key]
        rows.sort(key=lambda x: str(x.get("tool_name", "")))
        return rows
