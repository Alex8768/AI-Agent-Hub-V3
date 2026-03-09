from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.tool_safety.sandbox_policy import ToolSafetySandboxPolicy
from src.layers.pro.reasoning.tool_safety.tool_catalog import (
    ToolCatalogEntry,
    build_tool_catalog_entry,
)


class ToolSafetyDecision(TypedDict):
    tool_name: str
    allowed: bool
    reason: str
    mode: str
    risk_level: str
    requires_network: bool
    requires_filesystem: bool
    requires_execution: bool
    violated_constraints: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _tool_name_key(value: object) -> str:
    return _normalize_string(value).lower()


def _lookup_catalog_entry(
    *,
    tool_name: str,
    catalog: list[ToolCatalogEntry],
) -> ToolCatalogEntry:
    target = _tool_name_key(tool_name)
    for entry in list(catalog or []):
        if _tool_name_key((entry or {}).get("tool_name", "")) == target:
            return entry
    return build_tool_catalog_entry(tool_name=tool_name)


def build_tool_safety_decision(
    *,
    tool_name: object,
    policy: ToolSafetySandboxPolicy,
    catalog: list[ToolCatalogEntry],
) -> ToolSafetyDecision:
    """Build deterministic allow/deny decision from sandbox policy and catalog."""
    normalized_tool_name = _normalize_string(tool_name)
    entry = _lookup_catalog_entry(tool_name=normalized_tool_name, catalog=catalog)
    allow_set = {_tool_name_key(x) for x in list(policy.get("allowed_tools") or [])}
    deny_set = {_tool_name_key(x) for x in list(policy.get("denied_tools") or [])}
    mode = _normalize_string(policy.get("mode", "deny_by_default")) or "deny_by_default"

    violations: list[str] = []
    tool_key = _tool_name_key(normalized_tool_name)
    if not tool_key:
        violations.append("empty_tool_name")
    if tool_key in deny_set:
        violations.append("tool_explicitly_denied")
    if mode == "deny_by_default" and tool_key not in allow_set:
        violations.append("tool_not_allowlisted")
    if bool(entry.get("requires_network")) and not bool(policy.get("allow_network")):
        violations.append("network_required_but_disabled")

    ordered_violations = sorted(set(str(x) for x in violations))
    allowed = len(ordered_violations) == 0
    if allowed:
        reason = "allowed"
    else:
        reason = ordered_violations[0]

    return {
        "tool_name": normalized_tool_name,
        "allowed": allowed,
        "reason": reason,
        "mode": mode,
        "risk_level": str(entry.get("risk_level", "medium") or "medium"),
        "requires_network": bool(entry.get("requires_network", False)),
        "requires_filesystem": bool(entry.get("requires_filesystem", False)),
        "requires_execution": bool(entry.get("requires_execution", False)),
        "violated_constraints": ordered_violations,
    }


def build_tool_safety_decisions(
    *,
    tool_names: list[object],
    policy: ToolSafetySandboxPolicy,
    catalog: list[ToolCatalogEntry],
) -> list[ToolSafetyDecision]:
    """Build ordered tool safety decisions for multiple tool names."""
    decisions: list[ToolSafetyDecision] = []
    for raw in list(tool_names or []):
        decisions.append(
            build_tool_safety_decision(
                tool_name=raw,
                policy=policy,
                catalog=catalog,
            )
        )
    return decisions
