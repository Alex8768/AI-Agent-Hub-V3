"""Durable record key builders extracted from answer service."""

from __future__ import annotations

import hashlib


def durable_approval_record_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:durable:approval_session_record"


def durable_idempotency_record_key(*, session_id: str, idempotency_key: str = "") -> str:
    sid = str(session_id or "default")
    ikey = str(idempotency_key or "").strip()
    if ikey:
        return f"session:{sid}:durable:idempotency_record:{ikey}"
    return f"session:{sid}:durable:idempotency_record:last"


def run_execution_pilot_runtime(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    actions_enabled: bool,
    execution_pilot_allowlisted_action_types: tuple[str, ...],
    execution_pilot_max_approved_action_ids: int,
    is_allowlisted_action_type_fn: object,
) -> tuple[list[str], list[str]]:
    handshake = dict(handshake_bundle or {})
    if not actions_enabled:
        return [], ["pilot_runtime_disabled"]
    if str(handshake.get("state", "idle") or "idle") != "approved":
        return [], ["pilot_runtime_not_approved"]

    approved_action_ids = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    if not approved_action_ids:
        return [], ["pilot_runtime_no_approved_actions"]

    action_rows = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    action_type_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("action_type", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }
    rollback_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("rollback_plan", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }
    allowlisted_set = set(execution_pilot_allowlisted_action_types)
    eligible = [
        aid
        for aid in approved_action_ids
        if bool(is_allowlisted_action_type_fn(str(action_type_by_id.get(aid, "") or ""), allowlisted_set))
        and bool(str(rollback_by_id.get(aid, "") or "").strip())
    ]
    executed_action_ids = eligible[: int(execution_pilot_max_approved_action_ids)]
    if executed_action_ids:
        return executed_action_ids, ["pilot_runtime_executed"]
    return [], ["pilot_runtime_no_eligible_actions"]


def build_execution_receipt_stub(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
    executed_action_ids: list[str] | None,
    execution_receipt_contract_version: str,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    plan_id = str(plan_bundle.get("plan_id", "") or "")
    state = str(handshake.get("state", "idle") or "idle")
    approved = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    blocked = [str(x) for x in list(handshake.get("blocked_action_ids") or []) if str(x)]
    rollback_by_action_id = {
        str((row or {}).get("action_id", "") or ""): str((row or {}).get("rollback_plan", "") or "")
        for row in list(draft_actions_bundle.get("actions") or [])
        if str((row or {}).get("action_id", "") or "").strip()
    }
    rollback_required_action_ids = approved if state == "approved" else []
    rollback_ready_action_ids = [
        aid for aid in rollback_required_action_ids if str(rollback_by_action_id.get(aid, "") or "").strip()
    ]
    rollback_missing_action_ids = [
        aid for aid in rollback_required_action_ids if aid not in set(rollback_ready_action_ids)
    ]
    rollback_status = (
        "ready"
        if state == "approved" and not rollback_missing_action_ids
        else ("blocked_missing_rollback_plan" if state == "approved" else "not_applicable")
    )
    if not blocked:
        blocked = [
            str((row or {}).get("action_id", "") or "")
            for row in list(draft_actions_bundle.get("actions") or [])
            if str((row or {}).get("action_id", "") or "").strip()
            and str((row or {}).get("action_id", "") or "") not in set(approved)
        ]

    executed = [str(x) for x in list(executed_action_ids or []) if str(x)]
    if state in {"approved", "cancelled"}:
        seed = f"{workspace_id}|{request_id}|{plan_id}|{state}|{','.join(sorted(approved))}|{','.join(sorted(blocked))}"
        receipt_id = f"receipt:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
        status = "recorded"
        reason_codes = ["execution_receipt_stub_recorded"]
        if executed:
            reason_codes.append("pilot_runtime_execution_recorded")
    elif state == "pending_confirmation":
        receipt_id = ""
        status = "awaiting_confirmation"
        reason_codes = ["execution_receipt_pending_confirmation"]
    else:
        receipt_id = ""
        status = "idle"
        reason_codes = ["execution_receipt_not_ready"]

    return {
        "contract_version": str(execution_receipt_contract_version or ""),
        "receipt_id": receipt_id,
        "status": status,
        "handshake_state": state,
        "plan_id": plan_id,
        "approved_action_ids": approved,
        "blocked_action_ids": blocked,
        "executed_action_ids": executed,
        "rollback_status": rollback_status,
        "rollback_required_action_ids": rollback_required_action_ids,
        "rollback_ready_action_ids": rollback_ready_action_ids,
        "rollback_missing_action_ids": rollback_missing_action_ids,
        "reason_codes": reason_codes,
    }


def build_safe_mode_execution_gateway(
    *,
    handshake_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
    execution_gateway_contract_version: str,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    receipt = dict(receipt_bundle or {})
    state = str(handshake.get("state", "idle") or "idle")
    approved = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    blocked = [str(x) for x in list(handshake.get("blocked_action_ids") or []) if str(x)]
    if not actions_enabled:
        return {
            "contract_version": str(execution_gateway_contract_version or ""),
            "mode": "safe_mode",
            "state": "disabled",
            "safe_mode": True,
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "executed_action_ids": [],
            "dry_run_action_ids": [],
            "reason_codes": ["assistant_actions_disabled"],
        }
    if state == "approved":
        executed = [str(x) for x in list(receipt.get("executed_action_ids") or []) if str(x)]
        if executed:
            return {
                "contract_version": str(execution_gateway_contract_version or ""),
                "mode": "safe_mode",
                "state": "executed_in_pilot",
                "safe_mode": True,
                "approved_action_ids": approved,
                "blocked_action_ids": blocked,
                "executed_action_ids": executed,
                "dry_run_action_ids": [],
                "reason_codes": ["pilot_runtime_executed_no_external_side_effects"],
            }
        return {
            "contract_version": str(execution_gateway_contract_version or ""),
            "mode": "safe_mode",
            "state": "ready_for_execution",
            "safe_mode": True,
            "approved_action_ids": approved,
            "blocked_action_ids": blocked,
            "executed_action_ids": [],
            "dry_run_action_ids": approved,
            "reason_codes": ["execution_safe_mode_no_side_effects"],
        }
    if state == "cancelled":
        return {
            "contract_version": str(execution_gateway_contract_version or ""),
            "mode": "safe_mode",
            "state": "cancelled",
            "safe_mode": True,
            "approved_action_ids": [],
            "blocked_action_ids": blocked,
            "executed_action_ids": [],
            "dry_run_action_ids": [],
            "reason_codes": ["execution_cancelled_by_user"],
        }
    if str(receipt.get("status", "") or "") == "awaiting_confirmation":
        gateway_state = "awaiting_confirmation"
        reasons = ["execution_awaiting_confirmation"]
    else:
        gateway_state = "idle"
        reasons = ["execution_gateway_idle"]
    return {
        "contract_version": str(execution_gateway_contract_version or ""),
        "mode": "safe_mode",
        "state": gateway_state,
        "safe_mode": True,
        "approved_action_ids": approved,
        "blocked_action_ids": blocked,
        "executed_action_ids": [],
        "dry_run_action_ids": [],
        "reason_codes": reasons,
    }


def build_execution_pilot_bundle(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
    execution_pilot_contract_version: str,
    execution_pilot_allowlisted_action_types: tuple[str, ...],
    execution_pilot_max_approved_action_ids: int,
    is_allowlisted_action_type_fn: object,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    receipt = dict(receipt_bundle or {})
    requested_action_ids = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    executed_action_ids = [str(x) for x in list(receipt.get("executed_action_ids") or []) if str(x)]
    actions = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    action_type_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("action_type", "") or "")
        for row in actions
        if str(row.get("action_id", "") or "").strip()
    }
    allowed_action_types = list(execution_pilot_allowlisted_action_types)
    if not actions_enabled:
        return {
            "contract_version": str(execution_pilot_contract_version or ""),
            "mode": "controlled_pilot",
            "state": "disabled",
            "safe_mode": True,
            "execute_enabled": False,
            "max_actions_per_run": int(execution_pilot_max_approved_action_ids),
            "allowed_action_types": allowed_action_types,
            "requested_action_ids": requested_action_ids,
            "eligible_action_ids": [],
            "blocked_action_ids": [],
            "executed_action_ids": [],
            "reason_codes": ["assistant_actions_disabled"],
        }

    allowlisted_set = set(allowed_action_types)
    eligible = [
        aid
        for aid in requested_action_ids
        if bool(is_allowlisted_action_type_fn(str(action_type_by_id.get(aid, "") or ""), allowlisted_set))
    ]
    blocked = [aid for aid in requested_action_ids if aid not in set(eligible)]
    state = str(handshake.get("state", "idle") or "idle")
    if executed_action_ids:
        pilot_state = "executed"
        reasons = ["pilot_runtime_executed"]
    elif state == "pending_confirmation":
        pilot_state = "awaiting_confirmation"
        reasons = ["pilot_waiting_confirmation"]
    elif eligible:
        pilot_state = "ready"
        reasons = ["pilot_candidates_ready"]
    elif requested_action_ids:
        pilot_state = "blocked"
        reasons = ["pilot_action_type_not_allowlisted"]
    else:
        pilot_state = "idle"
        reasons = ["pilot_no_approved_actions"]
    return {
        "contract_version": str(execution_pilot_contract_version or ""),
        "mode": "controlled_pilot",
        "state": pilot_state,
        "safe_mode": True,
        "execute_enabled": False,
        "max_actions_per_run": int(execution_pilot_max_approved_action_ids),
        "allowed_action_types": allowed_action_types,
        "requested_action_ids": requested_action_ids,
        "eligible_action_ids": eligible[:1],
        "blocked_action_ids": blocked,
        "executed_action_ids": executed_action_ids,
        "reason_codes": reasons,
    }
