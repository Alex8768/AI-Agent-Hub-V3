"""Act read-only execution seam for answer runtime."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from src.core.config import get_settings
from src.services.answer.policy_profiles import resolve_runtime_policy_profile


_ACT_READ_ONLY_ALLOWLIST: tuple[str, ...] = ("list_files", "read_file")
_ACT_WRITE_CONFIRM_ALLOWLIST: tuple[str, ...] = ("save_file",)
_ACT_WRITE_CONFIRM_TTL_SECONDS = 900
_PENDING_WRITE_CONFIRMATIONS: dict[str, dict[str, object]] = {}
_WRITE_CONFIRM_IDEMPOTENCY: dict[str, dict[str, object]] = {}


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


def _build_scope_key(*, req: object, workspace_id: str) -> str:
    session_id = str(getattr(req, "session_id", "default") or "default")
    return f"{str(workspace_id or 'default')}:{session_id}"


def _issue_confirmation_token(*, scope_key: str, tool_name: str, tool_args: dict[str, object]) -> str:
    args_seed = str(sorted((str(k), str(v)) for k, v in dict(tool_args or {}).items()))
    seed = f"{scope_key}|{tool_name}|{args_seed}|{time.time_ns()}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
    return f"act-confirm:{digest}"


def _build_runtime_diag(
    *,
    status: str,
    mode: str,
    policy_profile: str,
    workspace_id: str,
    reason_codes: list[str],
    tool_name: str = "",
    confirmation: dict[str, object] | None = None,
    result: dict[str, object] | None = None,
    replayed: bool = False,
    error_type: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "mode": mode,
        "status": status,
        "policy_profile": policy_profile,
        "workspace_id": str(workspace_id or ""),
        "reason_codes": [str(x) for x in reason_codes if str(x)],
    }
    if tool_name:
        payload["tool_name"] = str(tool_name)
    if confirmation:
        payload["confirmation"] = dict(confirmation)
    if result is not None:
        payload["result"] = dict(result)
    if replayed:
        payload["replayed"] = True
    if error_type:
        payload["error_type"] = str(error_type)
    return payload


def _reset_act_write_runtime_state_for_tests() -> None:
    _PENDING_WRITE_CONFIRMATIONS.clear()
    _WRITE_CONFIRM_IDEMPOTENCY.clear()


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
    profile_name = str(policy_profile.get("profile_name", "") or "")
    selected_mode = str(route.get("selected_mode", "answer") or "answer")
    if selected_mode != "act":
        diagnostics["act_runtime"] = _build_runtime_diag(
            status="skipped",
            mode="disabled",
            policy_profile=profile_name,
            workspace_id=workspace_id,
            reason_codes=["act_mode_not_selected"],
        )
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
    if tool_name in _ACT_WRITE_CONFIRM_ALLOWLIST:
        write_policy = str(policy_profile.get("act_write_policy", "blocked") or "blocked")
        scope_key = _build_scope_key(req=req, workspace_id=workspace_id)
        filters = dict(getattr(req, "filters", None) or {})
        decision = str(filters.get("act_confirm_decision", "") or "").strip().lower()
        token = str(filters.get("act_confirmation_token", "") or "").strip()
        idempotency_key = str(filters.get("act_idempotency_key", "") or "").strip()
        pending = dict(_PENDING_WRITE_CONFIRMATIONS.get(scope_key) or {})
        now_epoch = int(time.time())

        if write_policy == "blocked":
            diagnostics["act_runtime"] = _build_runtime_diag(
                status="blocked",
                mode="write_confirm",
                policy_profile=profile_name,
                workspace_id=workspace_id,
                reason_codes=["act_write_blocked_by_policy_profile"],
                tool_name=tool_name,
            )
            diagnostics["runtime_policy_profile"] = dict(policy_profile)
            setattr(resp, "diagnostics", diagnostics)
            return resp

        if write_policy == "confirm_required":
            if decision not in {"approve", "cancel"}:
                issued_token = _issue_confirmation_token(scope_key=scope_key, tool_name=tool_name, tool_args=tool_args)
                expires_at = now_epoch + _ACT_WRITE_CONFIRM_TTL_SECONDS
                _PENDING_WRITE_CONFIRMATIONS[scope_key] = {
                    "confirmation_token": issued_token,
                    "tool_name": tool_name,
                    "tool_args": dict(tool_args),
                    "expires_at": expires_at,
                    "consumed": False,
                }
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="pending_confirmation",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_required"],
                    tool_name=tool_name,
                    confirmation={
                        "token": issued_token,
                        "expires_at": expires_at,
                        "ttl_seconds": _ACT_WRITE_CONFIRM_TTL_SECONDS,
                    },
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if not token:
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="blocked",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_token_missing"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if not pending or str(pending.get("confirmation_token", "")) != token:
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="blocked",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_token_invalid"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if bool(pending.get("consumed", False)):
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="blocked",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_token_consumed"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if int(pending.get("expires_at", 0) or 0) and now_epoch > int(pending.get("expires_at", 0) or 0):
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="blocked",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_token_expired"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if str(pending.get("tool_name", "")) != tool_name:
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="blocked",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_tool_mismatch"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if decision == "cancel":
                pending["consumed"] = True
                _PENDING_WRITE_CONFIRMATIONS[scope_key] = pending
                diagnostics["act_runtime"] = _build_runtime_diag(
                    status="cancelled",
                    mode="write_confirm",
                    policy_profile=profile_name,
                    workspace_id=workspace_id,
                    reason_codes=["act_write_confirmation_cancelled"],
                    tool_name=tool_name,
                )
                diagnostics["runtime_policy_profile"] = dict(policy_profile)
                setattr(resp, "diagnostics", diagnostics)
                return resp
            if idempotency_key:
                replay_key = f"{scope_key}:{idempotency_key}"
                prior = dict(_WRITE_CONFIRM_IDEMPOTENCY.get(replay_key) or {})
                if prior and str(prior.get("confirmation_token", "")) == token:
                    pending["consumed"] = True
                    _PENDING_WRITE_CONFIRMATIONS[scope_key] = pending
                    diagnostics["act_runtime"] = _build_runtime_diag(
                        status="executed",
                        mode="write_confirm",
                        policy_profile=profile_name,
                        workspace_id=workspace_id,
                        reason_codes=["act_write_confirmation_replayed"],
                        tool_name=tool_name,
                        result=dict(prior.get("result", {}) or {}),
                        replayed=True,
                    )
                    diagnostics["runtime_policy_profile"] = dict(policy_profile)
                    setattr(resp, "diagnostics", diagnostics)
                    return resp

            tool_args = dict(pending.get("tool_args") or tool_args)

    if tool_name not in _ACT_READ_ONLY_ALLOWLIST:
        if tool_name not in _ACT_WRITE_CONFIRM_ALLOWLIST:
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
        # write-confirm allowlisted tool continues to invoker path below.
    elif tool_name == "read_file" and not str(tool_args.get("path", "") or "").strip():
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
        mode = "write_confirm" if tool_name in _ACT_WRITE_CONFIRM_ALLOWLIST else "read_only"
        reason = "act_write_tool_failed" if mode == "write_confirm" else "act_read_only_tool_failed"
        diagnostics["act_runtime"] = {
            "mode": mode,
            "status": "failed",
            "policy_profile": str(policy_profile.get("profile_name", "")),
            "tool_name": tool_name,
            "workspace_id": str(workspace_id or ""),
            "reason_codes": [reason],
            "error_type": type(exc).__name__,
        }
        diagnostics["runtime_policy_profile"] = dict(policy_profile)
        setattr(resp, "diagnostics", diagnostics)
        return resp

    runtime_result = result if isinstance(result, dict) else {"value": result}
    if tool_name in _ACT_WRITE_CONFIRM_ALLOWLIST:
        scope_key = _build_scope_key(req=req, workspace_id=workspace_id)
        filters = dict(getattr(req, "filters", None) or {})
        decision = str(filters.get("act_confirm_decision", "") or "").strip().lower()
        token = str(filters.get("act_confirmation_token", "") or "").strip()
        idempotency_key = str(filters.get("act_idempotency_key", "") or "").strip()
        pending = dict(_PENDING_WRITE_CONFIRMATIONS.get(scope_key) or {})
        if decision == "approve" and pending:
            pending["consumed"] = True
            _PENDING_WRITE_CONFIRMATIONS[scope_key] = pending
        if decision == "approve" and idempotency_key and token:
            _WRITE_CONFIRM_IDEMPOTENCY[f"{scope_key}:{idempotency_key}"] = {
                "confirmation_token": token,
                "result": dict(runtime_result),
            }
        reason_code = "act_write_tool_executed_confirmed" if decision == "approve" else "act_write_tool_executed_direct"
        diagnostics["act_runtime"] = _build_runtime_diag(
            status="executed",
            mode="write_confirm",
            policy_profile=profile_name,
            workspace_id=workspace_id,
            reason_codes=[reason_code],
            tool_name=tool_name,
            result=runtime_result,
        )
    else:
        diagnostics["act_runtime"] = _build_runtime_diag(
            status="executed",
            mode="read_only",
            policy_profile=profile_name,
            workspace_id=workspace_id,
            reason_codes=["act_read_only_tool_executed"],
            tool_name=tool_name,
            result=runtime_result,
        )
    diagnostics["runtime_policy_profile"] = dict(policy_profile)
    setattr(resp, "diagnostics", diagnostics)
    return resp
