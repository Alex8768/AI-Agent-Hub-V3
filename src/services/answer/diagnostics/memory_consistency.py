"""Memory consistency diagnostics helpers extracted from answer service."""

from __future__ import annotations


def build_memory_consistency_bundle(
    *,
    session_memory_loaded: bool,
    session_memory_hit: bool,
    durable_approval_record_loaded: bool,
    durable_idempotency_record_loaded: bool,
) -> dict[str, object]:
    reason_codes: list[str] = ["memory_consistency_guard_evaluated"]
    if not session_memory_loaded:
        reason_codes.append("memory_consistency_store_unavailable")
    if session_memory_hit:
        reason_codes.append("memory_consistency_session_hit")
    if durable_approval_record_loaded:
        reason_codes.append("memory_consistency_durable_approval_loaded")
    if durable_idempotency_record_loaded:
        reason_codes.append("memory_consistency_durable_idempotency_loaded")
    status = "warn" if not session_memory_loaded else "ok"
    return {
        "contract_version": "v1",
        "mode": "memory_consistency_guarded",
        "status": status,
        "inputs": {
            "session_memory_loaded": bool(session_memory_loaded),
            "session_memory_hit": bool(session_memory_hit),
            "durable_approval_record_loaded": bool(durable_approval_record_loaded),
            "durable_idempotency_record_loaded": bool(durable_idempotency_record_loaded),
        },
        "reason_codes": sorted(set(reason_codes)),
    }


def build_memory_consistency_strategy_contract() -> dict[str, object]:
    reason_codes = [
        "memory_consistency_strategy_contract_defined",
        "memory_consistency_strategy_best_effort",
        "memory_consistency_strategy_outbox_deferred",
        "memory_consistency_strategy_compensation_deferred",
    ]
    return {
        "contract_version": "v1",
        "mode": "best_effort_dual_store",
        "consistency_target": "eventual_consistency",
        "write_strategy": "sqlite_primary_qdrant_best_effort",
        "outbox_strategy": "deferred",
        "compensation_strategy": "deferred",
        "reason_codes": sorted(set(reason_codes)),
    }
