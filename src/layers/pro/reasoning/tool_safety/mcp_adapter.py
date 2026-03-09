from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.tool_catalog import ToolCatalogEntry, build_tool_catalog_entry
from src.mcp_protocol.registry import MCPToolSpec, build_mcp_tool_spec


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw).lower()
        if item:
            rows.append(item)
    return sorted(set(rows))


def _infer_risk_level(*, tags: list[str], tool_name: str, description: str) -> str:
    joined = " ".join([tool_name.lower(), description.lower(), *tags])
    if any(token in joined for token in ["delete", "remove", "execute", "shell", "write"]):
        return "high"
    if any(token in joined for token in ["http", "network", "remote"]):
        return "medium"
    return "low"


def _infer_capabilities(*, tags: list[str], tool_name: str, description: str) -> list[str]:
    caps: list[str] = ["read"]
    joined = " ".join([tool_name.lower(), description.lower(), *tags])
    if any(token in joined for token in ["write", "save", "create"]):
        caps.append("write")
    if any(token in joined for token in ["execute", "shell", "run"]):
        caps.append("execute")
    if any(token in joined for token in ["network", "http", "remote"]):
        caps.append("network")
    return sorted(set(caps))


def build_tool_catalog_entry_from_mcp_tool(
    *,
    mcp_tool: MCPToolSpec | dict[str, object],
) -> ToolCatalogEntry:
    row = dict(mcp_tool or {})
    tool = build_mcp_tool_spec(
        tool_name=row.get("tool_name", ""),
        server_name=row.get("server_name", ""),
        description=row.get("description", ""),
        input_schema=row.get("input_schema", {}),
        tags=row.get("tags", []),
        enabled=row.get("enabled", True),
    )
    tags = _normalize_string_list(tool.get("tags", []))
    description = str(tool.get("description", "") or "")
    tool_name = str(tool.get("tool_name", "") or "")
    capabilities = _infer_capabilities(tags=tags, tool_name=tool_name, description=description)
    risk_level = _infer_risk_level(tags=tags, tool_name=tool_name, description=description)
    requires_network = "network" in capabilities
    requires_execution = "execute" in capabilities
    requires_filesystem = not requires_network or "write" in capabilities or "read" in capabilities
    return build_tool_catalog_entry(
        tool_name=tool_name,
        risk_level=risk_level,
        capabilities=capabilities,
        requires_network=requires_network,
        requires_filesystem=requires_filesystem,
        requires_execution=requires_execution,
    )


def build_tool_catalog_from_mcp_tools(
    *,
    mcp_tools: list[MCPToolSpec] | list[dict[str, object]],
) -> list[ToolCatalogEntry]:
    rows: list[ToolCatalogEntry] = []
    for raw in list(mcp_tools or []):
        entry = build_tool_catalog_entry_from_mcp_tool(mcp_tool=raw)
        if not str(entry.get("tool_name", "")).strip():
            continue
        rows.append(entry)
    rows.sort(key=lambda x: str(x.get("tool_name", "")))
    return rows
