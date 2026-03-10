from __future__ import annotations


def build_governance_subcore_bundle(
    *,
    reasoning_trace: dict[str, object],
    reasoning_timeline: dict[str, object],
    execution_receipt: dict[str, object],
) -> dict[str, object]:
    trace_present = bool(reasoning_trace)
    timeline_events = list(reasoning_timeline.get("events") or []) if isinstance(reasoning_timeline, dict) else []
    receipt_status = str(execution_receipt.get("status", "idle") or "idle") if isinstance(execution_receipt, dict) else "idle"

    reason_codes: list[str] = ["governance_subcore_runtime_wired"]
    if trace_present:
        reason_codes.append("governance_subcore_trace_present")
    if timeline_events:
        reason_codes.append("governance_subcore_timeline_present")
    if receipt_status != "idle":
        reason_codes.append("governance_subcore_receipt_active")

    return {
        "contract_version": "v1",
        "mode": "governance_subcore",
        "status": "ready",
        "trace_status": "present" if trace_present else "missing",
        "timeline_status": "present" if timeline_events else "idle",
        "receipt_status": receipt_status,
        "replay_status": "available_via_receipt",
        "reason_codes": sorted(set(reason_codes)),
    }
