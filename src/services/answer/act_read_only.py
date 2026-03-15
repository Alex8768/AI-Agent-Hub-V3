"""Act read-only execution seam for answer runtime."""

from __future__ import annotations

from typing import Any

from src.core.config import get_settings
from src.services.answer.policy_profiles import resolve_runtime_policy_profile


_ACT_READ_ONLY_ALLOWLIST: tuple[str, ...] = ("list_files", "read_file")


def _resolve_act_request(req: object) -> tuple[str, dict[str, object]]:
    filters = dict(getattr(req, "filters", None) or {})
    raw_tool = filters.get("act_tool_name", filters.get("act_tool", filters.get("tool_name", "")))
    tool_name = str(raw_tool or "").strip()
    raw_args = filters.get("act_tool_args", filters.get("tool_args", {}))
    tool_args = dict(raw_args or {}) if isinstance(raw_args, dict) else {}
    if not tool_name:
        tool_name = "list_files"
        tool_args = {"path": "."}
    return tool_name, tool_args


async def apply_act_read_only_runtime(
    *,
    resp: object,
    req: object,
    http: object,
    workspace_id: str,
    route: dict[str, object],
) -> object:
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    policy_profile = resolve_runtime_policy_profile(req=req, settings=get_settings())
    selected_mode = str(route.get("selected_mode", "answer") or "answer")
    if selected_mode != "act":
        diagnostics["act_runtime"] = {
            "mode": "disabled",
            "status": "skipped",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "reason_codes": ["act_mode_not_selected"],
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp
    if not bool(policy_profile.get("allow_act_read_only", False)):
        diagnostics["act_runtime"] = {
            "mode": "read_only",
            "status": "blocked",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "workspace_id": str(workspace_id or ""),
            "reason_codes": ["act_blocked_by_policy_profile"],
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp

    tool_name, tool_args = _resolve_act_request(req)
    if tool_name not in _ACT_READ_ONLY_ALLOWLIST:
        diagnostics["act_runtime"] = {
            "mode": "read_only",
            "status": "blocked",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "tool_name": tool_name,
            "workspace_id": str(workspace_id or ""),
            "reason_codes": ["act_read_only_tool_not_allowlisted"],
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp
    if tool_name == "read_file" and not str(tool_args.get("path", "") or "").strip():
        diagnostics["act_runtime"] = {
            "mode": "read_only",
            "status": "blocked",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "tool_name": tool_name,
            "workspace_id": str(workspace_id or ""),
            "reason_codes": ["act_read_only_missing_path"],
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp

    invoker = getattr(getattr(http, "app", None), "state", None)
    invoker = getattr(invoker, "mcp_tool_invoker", None)
    if not callable(invoker):
        diagnostics["act_runtime"] = {
            "mode": "read_only",
            "status": "blocked",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "tool_name": tool_name,
            "workspace_id": str(workspace_id or ""),
            "reason_codes": ["act_read_only_invoker_unavailable"],
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp

    try:
        result = await invoker(tool_name=tool_name, arguments=tool_args)
    except Exception as exc:
        diagnostics["act_runtime"] = {
            "mode": "read_only",
            "status": "failed",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "tool_name": tool_name,
            "workspace_id": str(workspace_id or ""),
            "reason_codes": ["act_read_only_tool_failed"],
            "error_type": type(exc).__name__,
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp

    diagnostics["act_runtime"] = {
        "mode": "read_only",
        "status": "executed",
        "policy_profile": str(policy_profile.get("profile_name", "")),
        "tool_name": tool_name,
        "workspace_id": str(workspace_id or ""),
        "reason_codes": ["act_read_only_tool_executed"],
        "result": result if isinstance(result, dict) else {"value": result},
    }
    diagnostics["runtime_policy_profile"] = dict(policy_profile)
    setattr(resp, "diagnostics", diagnostics)
    return resp
