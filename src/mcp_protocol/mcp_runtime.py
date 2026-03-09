from __future__ import annotations

import inspect
from typing import Protocol, TypedDict

from src.layers.pro.reasoning.tool_safety.decision_engine import ToolSafetyDecision, build_tool_safety_decision
from src.layers.pro.reasoning.tool_safety.mcp_adapter import build_tool_catalog_entry_from_mcp_tool
from src.layers.pro.reasoning.tool_safety.sandbox_policy import (
    ToolSafetySandboxPolicy,
    build_tool_safety_sandbox_policy,
)
from src.layers.pro.reasoning.tool_safety.tool_catalog import ToolCatalogEntry
from src.mcp_protocol.registry import MCPToolRegistry


class MCPRuntimeReceipt(TypedDict):
    tool_name: str
    status: str
    allowed: bool
    reason_codes: list[str]
    tool_safety_decision: ToolSafetyDecision


class MCPRuntimeResult(TypedDict):
    receipt: MCPRuntimeReceipt
    result: dict[str, object]
    error: str


class MCPToolInvoker(Protocol):
    def __call__(self, *, tool_name: str, arguments: dict[str, object]) -> object:
        """Invoke MCP tool by name with arguments."""


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


async def _call_invoker(
    *,
    invoker: MCPToolInvoker,
    tool_name: str,
    arguments: dict[str, object],
) -> object:
    raw = invoker(tool_name=tool_name, arguments=arguments)
    if inspect.isawaitable(raw):
        return await raw
    return raw


async def execute_mcp_tool_with_safety(
    *,
    registry: MCPToolRegistry,
    tool_name: object,
    arguments: object = None,
    invoker: MCPToolInvoker | None = None,
    policy: ToolSafetySandboxPolicy | None = None,
    catalog: list[ToolCatalogEntry] | None = None,
) -> MCPRuntimeResult:
    normalized_tool_name = _normalize_string(tool_name)
    tool = registry.get_tool(normalized_tool_name)
    if not tool:
        decision = build_tool_safety_decision(
            tool_name=normalized_tool_name,
            policy=policy or build_tool_safety_sandbox_policy(),
            catalog=list(catalog or []),
        )
        return {
            "receipt": {
                "tool_name": normalized_tool_name,
                "status": "blocked",
                "allowed": False,
                "reason_codes": ["tool_not_registered"],
                "tool_safety_decision": decision,
            },
            "result": {},
            "error": "Tool not registered",
        }

    derived_entry = build_tool_catalog_entry_from_mcp_tool(mcp_tool=tool)
    active_catalog = list(catalog or []) + [derived_entry]
    if policy is not None:
        active_policy = policy
    else:
        default_policy = build_tool_safety_sandbox_policy()
        allowlisted = list(default_policy.get("allowed_tools") or [])
        safe_to_allow = (
            str(derived_entry.get("risk_level", "") or "") in {"low", "medium"}
            and not bool(derived_entry.get("requires_execution", False))
        )
        if safe_to_allow:
            allowlisted.append(normalized_tool_name)
        active_policy = build_tool_safety_sandbox_policy(
            mode=default_policy.get("mode", "deny_by_default"),
            allowed_tools=allowlisted,
            denied_tools=default_policy.get("denied_tools", []),
            allowed_path_prefixes=default_policy.get("allowed_path_prefixes", []),
            allow_network=default_policy.get("allow_network", False),
            max_execution_seconds=default_policy.get("max_execution_seconds", 30),
        )
    decision = build_tool_safety_decision(
        tool_name=normalized_tool_name,
        policy=active_policy,
        catalog=active_catalog,
    )
    if not bool(decision.get("allowed", False)):
        return {
            "receipt": {
                "tool_name": normalized_tool_name,
                "status": "blocked",
                "allowed": False,
                "reason_codes": ["tool_safety_blocked"],
                "tool_safety_decision": decision,
            },
            "result": {},
            "error": str(decision.get("reason", "") or "blocked"),
        }

    if invoker is None:
        return {
            "receipt": {
                "tool_name": normalized_tool_name,
                "status": "failed",
                "allowed": True,
                "reason_codes": ["invoker_unavailable"],
                "tool_safety_decision": decision,
            },
            "result": {},
            "error": "Invoker unavailable",
        }

    try:
        payload = await _call_invoker(
            invoker=invoker,
            tool_name=normalized_tool_name,
            arguments=dict(arguments) if isinstance(arguments, dict) else {},
        )
        result = dict(payload) if isinstance(payload, dict) else {"output": payload}
        return {
            "receipt": {
                "tool_name": normalized_tool_name,
                "status": "succeeded",
                "allowed": True,
                "reason_codes": [],
                "tool_safety_decision": decision,
            },
            "result": result,
            "error": "",
        }
    except Exception as exc:
        return {
            "receipt": {
                "tool_name": normalized_tool_name,
                "status": "failed",
                "allowed": True,
                "reason_codes": ["invocation_failed"],
                "tool_safety_decision": decision,
            },
            "result": {},
            "error": _normalize_string(exc),
        }
