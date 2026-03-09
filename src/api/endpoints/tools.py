from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.core.config import get_settings
from src.mcp_protocol import MCPToolRegistry, build_mcp_tool_discovery_payload, execute_mcp_tool_with_safety

router = APIRouter(tags=["Tools"])


def _get_registry(http: Request) -> MCPToolRegistry:
    registry = getattr(getattr(http, "app", None), "state", None)
    current = getattr(registry, "mcp_registry", None) if registry is not None else None
    if isinstance(current, MCPToolRegistry):
        return current
    fresh = MCPToolRegistry()
    if registry is not None:
        setattr(registry, "mcp_registry", fresh)
    return fresh


@router.get("/api/v1/tools")
async def list_tools(http: Request):
    s = get_settings()
    if not bool(getattr(s, "feature_reasoning_api", False)):
        raise HTTPException(status_code=404, detail="Not Found")
    registry = _get_registry(http)
    payload = build_mcp_tool_discovery_payload(
        tools=registry.list_tools(enabled_only=False),
        servers=registry.list_servers(enabled_only=False),
    )
    return payload


@router.get("/api/v1/tools/{tool_name}")
async def get_tool_schema(http: Request, tool_name: str):
    s = get_settings()
    if not bool(getattr(s, "feature_reasoning_api", False)):
        raise HTTPException(status_code=404, detail="Not Found")
    registry = _get_registry(http)
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return dict(tool)


@router.post("/api/v1/tools/{tool_name}/invoke")
async def invoke_tool(http: Request, tool_name: str, payload: dict[str, object] | None = None):
    s = get_settings()
    if not bool(getattr(s, "feature_reasoning_api", False)):
        raise HTTPException(status_code=404, detail="Not Found")
    registry = _get_registry(http)
    app_state = getattr(getattr(http, "app", None), "state", None)
    invoker = getattr(app_state, "mcp_tool_invoker", None) if app_state is not None else None
    arguments = dict((payload or {}).get("arguments") or {}) if isinstance(payload, dict) else {}
    runtime = await execute_mcp_tool_with_safety(
        registry=registry,
        tool_name=tool_name,
        arguments=arguments,
        invoker=invoker,
    )
    receipt = dict(runtime.get("receipt") or {})
    status = str(receipt.get("status", "") or "")
    if status == "blocked":
        raise HTTPException(status_code=403, detail=str(runtime.get("error", "") or "Tool blocked"))
    if status == "failed":
        raise HTTPException(status_code=503, detail=str(runtime.get("error", "") or "Tool invocation failed"))
    return runtime
