from __future__ import annotations


def normalize_execution_request(*, filters: dict[str, object]) -> dict[str, object]:
    decision_raw = str(filters.get("handshake_decision", "") or "").strip().lower()
    if decision_raw not in {"approve", "cancel"}:
        decision_raw = ""

    token = str(filters.get("handshake_confirmation_token", "") or "").strip()
    requested_action_ids_raw = list(filters.get("handshake_action_ids") or [])
    requested_action_ids = [str(x).strip() for x in requested_action_ids_raw if str(x or "").strip()]
    idempotency_key = str(filters.get("handshake_idempotency_key", "") or "").strip()
    return {
        "decision": decision_raw,
        "confirmation_token": token,
        "requested_action_ids": requested_action_ids,
        "idempotency_key": idempotency_key,
    }


def build_execution_request_boundary_bundle(
    *,
    execution_request: dict[str, object],
    transition_policy: dict[str, object],
) -> dict[str, object]:
    decision = str(execution_request.get("decision", "") or "")
    requested_action_ids = [str(x) for x in list(execution_request.get("requested_action_ids") or []) if str(x)]
    token = str(execution_request.get("confirmation_token", "") or "")
    idempotency_key = str(execution_request.get("idempotency_key", "") or "")
    reason_codes: list[str] = ["execution_request_boundary_runtime_wired"]
    if decision:
        reason_codes.append(f"execution_request_decision:{decision}")
    if requested_action_ids:
        reason_codes.append("execution_request_action_filter_present")
    if token:
        reason_codes.append("execution_request_confirmation_token_present")
    if idempotency_key:
        reason_codes.append("execution_request_idempotency_key_present")

    return {
        "contract_version": "v1",
        "mode": "execution_request_boundary",
        "status": "ready" if decision else "idle",
        "decision": decision,
        "requested_action_ids_count": int(len(requested_action_ids)),
        "has_confirmation_token": bool(token),
        "idempotency_key_present": bool(idempotency_key),
        "transition_policy_mode": str(transition_policy.get("mode", "") or ""),
        "reason_codes": sorted(set(reason_codes)),
    }
