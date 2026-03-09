from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.enterprise.readiness_contract import (
    EnterpriseReadinessContract,
    build_enterprise_readiness_contract,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    EnterpriseReleaseGatePolicy,
    build_enterprise_release_gate_policy,
)


class EnterpriseRolloutDecision(TypedDict):
    decision_id: str
    action: str
    target_environment: str
    blocked_by: list[str]
    reason_codes: list[str]
    confidence: float
    requires_human_approval: bool


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def _normalize_action(value: object) -> str:
    action = _normalize_string(value).lower()
    if action not in {"approve", "defer", "reject"}:
        return "defer"
    return action


def build_enterprise_rollout_decision(
    *,
    decision_id: object,
    action: object,
    target_environment: object = "production",
    blocked_by: object = None,
    reason_codes: object = None,
    confidence: object = 0.0,
    requires_human_approval: object = False,
) -> EnterpriseRolloutDecision:
    """Build normalized enterprise rollout decision contract."""
    return {
        "decision_id": _normalize_string(decision_id),
        "action": _normalize_action(action),
        "target_environment": _normalize_string(target_environment) or "production",
        "blocked_by": _normalize_string_list(blocked_by),
        "reason_codes": _normalize_string_list(reason_codes),
        "confidence": _normalize_float_01(confidence, default=0.0),
        "requires_human_approval": bool(requires_human_approval),
    }


def decide_enterprise_rollout_action(
    *,
    readiness: EnterpriseReadinessContract,
    policy: EnterpriseReleaseGatePolicy,
    decision_id: object = "enterprise_rollout_decision",
    target_environment: object = "production",
) -> EnterpriseRolloutDecision:
    """Decide approve/defer/reject for enterprise rollout from readiness + policy."""
    normalized_readiness = build_enterprise_readiness_contract(
        profile_name=readiness.get("profile_name", "default"),
        release_gate_passed=readiness.get("release_gate_passed", False),
        failed_checks=readiness.get("failed_checks", []),
        benchmark_pass_rate=readiness.get("benchmark_pass_rate", 0.0),
        benchmark_average_score=readiness.get("benchmark_average_score", 0.0),
        optimization_action=readiness.get("optimization_action", "defer"),
        optimization_requires_review=readiness.get("optimization_requires_review", False),
        warnings_count=readiness.get("warnings_count", 0),
        reason_codes=readiness.get("reason_codes", []),
    )
    normalized_policy = build_enterprise_release_gate_policy(
        profile_name=policy.get("profile_name", "default"),
        required_checks=policy.get("required_checks", []),
        blocking_checks=policy.get("blocking_checks", []),
        minimum_pass_rate=policy.get("minimum_pass_rate", 0.9),
        minimum_average_score=policy.get("minimum_average_score", 0.8),
        minimum_coverage_ratio=policy.get("minimum_coverage_ratio", 0.0),
        allow_skipped=policy.get("allow_skipped", False),
        require_benchmark_summary=policy.get("require_benchmark_summary", True),
        require_optimization_review=policy.get("require_optimization_review", True),
        allowed_warning_codes=policy.get("allowed_warning_codes", []),
    )

    blocked_by = list(normalized_readiness.get("failed_checks") or [])
    reasons = [str(x) for x in list(normalized_readiness.get("reason_codes") or [])]
    release_gate_passed = bool(normalized_readiness.get("release_gate_passed", False))
    optimization_action = str(normalized_readiness.get("optimization_action", "defer") or "defer")
    optimization_requires_review = bool(
        normalized_readiness.get("optimization_requires_review", False)
    )
    warnings_count = int(normalized_readiness.get("warnings_count", 0) or 0)

    if not release_gate_passed:
        action = "reject"
        reasons.append("release_gate_not_passed")
    elif optimization_action == "reject":
        action = "reject"
        reasons.append("optimization_rejected")
    elif (
        bool(normalized_policy.get("require_optimization_review", True))
        and optimization_requires_review
    ):
        action = "defer"
        reasons.append("manual_optimization_review_required")
    elif warnings_count > 0 and not bool(normalized_policy.get("allow_skipped", False)):
        action = "defer"
        reasons.append("warnings_present_policy_block")
    else:
        action = "approve"
        reasons.append("enterprise_gate_satisfied")

    confidence = float(normalized_readiness.get("readiness_score", 0.0) or 0.0)
    if action == "reject":
        confidence *= 0.5
    if action == "defer":
        confidence *= 0.8

    return build_enterprise_rollout_decision(
        decision_id=decision_id,
        action=action,
        target_environment=target_environment,
        blocked_by=blocked_by,
        reason_codes=reasons,
        confidence=confidence,
        requires_human_approval=bool(action != "approve"),
    )
