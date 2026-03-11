"""Runtime diagnostics contract helpers extracted from reasoning engine."""

from __future__ import annotations

from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN,
    SELF_CHECK_MISSING_MINIMAL_COUNT_MAX,
    VERIFY_DIAGNOSTICS_VERSION,
    VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED,
    VERIFY_SELF_CHECK_REASONS_COUNT_MAX,
    VERIFY_SELF_CHECK_STATUS_REQUIRED,
)


def evidence_summary(provenance: list) -> dict[str, object]:
    origins: dict[str, int] = {}
    rel_vals: list[float] = []
    for p in provenance or []:
        origin = str(getattr(p, "origin", "unknown") or "unknown")
        origins[origin] = int(origins.get(origin, 0)) + 1
        rel = getattr(p, "reliability", None)
        if isinstance(rel, (int, float)):
            rel_vals.append(float(rel))
    avg = (sum(rel_vals) / len(rel_vals)) if rel_vals else None
    return {
        "origin_counts": origins,
        "reliability_avg": avg,
        "count": int(len(provenance or [])),
    }


def evidence_contract_status(provenance: list) -> dict[str, object]:
    total = int(len(provenance or []))
    with_source_refs = 0
    with_known_origin = 0
    with_reliability = 0
    for p in provenance or []:
        if list(getattr(p, "source_refs", []) or []):
            with_source_refs += 1
        if str(getattr(p, "origin", "unknown") or "unknown") != "unknown":
            with_known_origin += 1
        rel = getattr(p, "reliability", None)
        if isinstance(rel, (int, float)):
            with_reliability += 1
    denom = float(total) if total > 0 else 1.0
    missing_minimal_fields: list[str] = []
    if total <= 0:
        missing_minimal_fields.extend(["source_refs", "origin"])
    else:
        if with_source_refs <= 0:
            missing_minimal_fields.append("source_refs")
        if with_known_origin <= 0:
            missing_minimal_fields.append("origin")
    minimal_coverage_score = float(
        (float(with_source_refs > 0) + float(with_known_origin > 0)) / 2.0
        if total > 0
        else 0.0
    )
    return {
        "version": EVIDENCE_CONTRACT_VERSION,
        "minimal_requirements": {
            "min_total": 1,
            "requires_source_refs": True,
            "requires_known_origin": True,
        },
        "total": total,
        "with_source_refs": with_source_refs,
        "with_known_origin": with_known_origin,
        "with_reliability": with_reliability,
        "source_refs_coverage": float(with_source_refs / denom) if total > 0 else 0.0,
        "known_origin_coverage": float(with_known_origin / denom) if total > 0 else 0.0,
        "reliability_coverage": float(with_reliability / denom) if total > 0 else 0.0,
        "missing_minimal_fields": missing_minimal_fields,
        "missing_minimal_count": int(len(missing_minimal_fields)),
        "minimal_coverage_score": minimal_coverage_score,
        "valid_minimal": bool(total > 0 and with_source_refs > 0 and with_known_origin > 0),
    }


def evidence_contract_gate_reason(contract: dict[str, object]) -> str:
    if bool(contract.get("valid_minimal", False)):
        return "ok"
    missing = list(contract.get("missing_minimal_fields") or [])
    if missing:
        return "missing:" + ",".join(str(x) for x in missing)
    return "invalid"


def self_check_diagnostics(contract: dict[str, object]) -> dict[str, object]:
    minimal_coverage_score = float(contract.get("minimal_coverage_score") or 0.0)
    missing_minimal_count = int(len(contract.get("missing_minimal_fields") or []))
    coverage_ok = minimal_coverage_score >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
    missing_ok = missing_minimal_count <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
    missing = list(contract.get("missing_minimal_fields") or [])
    if coverage_ok and missing_ok:
        status = "pass"
        reasons: list[str] = []
    else:
        reasons = []
        if not coverage_ok:
            reasons.append(
                f"threshold:minimal_coverage_score<{float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN):.1f}"
            )
        if not missing_ok:
            reasons.append(
                f"threshold:missing_minimal_count>{int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)}"
            )
        status = "warn"
    return {
        "version": "v1",
        "status": status,
        "reasons": reasons,
        "policy_mode": "warning_only",
        "inputs": {
            "evidence_contract_valid_minimal": bool(contract.get("valid_minimal", False)),
            "evidence_contract_missing_minimal_count": missing_minimal_count,
            "evidence_contract_minimal_coverage_score": minimal_coverage_score,
        },
        "thresholds": {
            "minimal_coverage_score_min": float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN),
            "missing_minimal_count_max": int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX),
            "missing_minimal_fields": missing,
        },
    }


def verify_diagnostics_preflight(*, planner_path_used: bool, self_check: dict[str, object]) -> dict[str, object]:
    self_check_status = str(self_check.get("status", "") or "")
    self_check_policy_mode = str(self_check.get("policy_mode", "") or "")
    self_check_reasons_count = int(len(self_check.get("reasons") or []))
    reasons: list[str] = []
    if self_check_status != str(VERIFY_SELF_CHECK_STATUS_REQUIRED):
        reasons.append(f"self_check_status!={VERIFY_SELF_CHECK_STATUS_REQUIRED}")
    if self_check_policy_mode != str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED):
        reasons.append(f"self_check_policy_mode!={VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED}")
    if self_check_reasons_count > int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX):
        reasons.append(f"self_check_reasons_count>{int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)}")
    status = "pass" if not reasons else "warn"
    return {
        "version": VERIFY_DIAGNOSTICS_VERSION,
        "status": status,
        "reasons": reasons,
        "policy_mode": "warning_only",
        "inputs": {
            "planner_path_used": bool(planner_path_used),
            "self_check_status": self_check_status,
            "self_check_policy_mode": self_check_policy_mode,
            "self_check_reasons_count": self_check_reasons_count,
        },
        "thresholds": {
            "required_self_check_status": str(VERIFY_SELF_CHECK_STATUS_REQUIRED),
            "required_self_check_policy_mode": str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED),
            "self_check_reasons_count_max": int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX),
        },
    }


def build_planner_runtime_parity_diagnostics(
    *,
    planner_path_used: bool,
    planner_step_count: int,
    observed_action: str,
    observed_step: int,
) -> dict[str, object]:
    reasons: list[str] = ["planner_runtime_parity_evaluated"]
    status = "pass"
    action = str(observed_action or "").strip()
    step_idx = int(observed_step or 0)
    max_step_index = max(int(planner_step_count) - 1, 0)
    if not action:
        status = "warn"
        reasons.append("planner_runtime_action_missing")
    else:
        reasons.append("planner_runtime_action_present")
    if step_idx < 0 or (int(planner_step_count) > 0 and step_idx > max_step_index):
        status = "warn"
        reasons.append("planner_runtime_step_out_of_bounds")
    else:
        reasons.append("planner_runtime_step_in_bounds")
    if planner_path_used:
        reasons.append("planner_runtime_graph_path")
    else:
        reasons.append("planner_runtime_fallback_path")
    return {
        "contract_version": "v1",
        "mode": "planner_runtime_parity_guarded",
        "status": status,
        "inputs": {
            "planner_path_used": bool(planner_path_used),
            "planner_step_count": int(planner_step_count),
            "observed_action": action,
            "observed_step": int(step_idx),
        },
        "thresholds": {
            "action_required": True,
            "step_index_min": 0,
            "step_index_max": int(max_step_index),
        },
        "reason_codes": sorted(set(reasons)),
    }


def apply_reasoning_runtime_warning_flags(
    *,
    warnings: list[str],
    verify: dict[str, object],
    self_check: dict[str, object],
    contract: dict[str, object],
) -> list[str]:
    rows = [str(x) for x in list(warnings or []) if str(x)]
    if str(verify.get("status", "")) == "warn" and "verify_warning" not in rows:
        rows.append("verify_warning")
    if str(self_check.get("status", "")) == "warn" and "self_check_warning" not in rows:
        rows.append("self_check_warning")
    if not bool(contract.get("valid_minimal", False)) and "evidence_contract_minimal_invalid" not in rows:
        rows.append("evidence_contract_minimal_invalid")
    return rows
