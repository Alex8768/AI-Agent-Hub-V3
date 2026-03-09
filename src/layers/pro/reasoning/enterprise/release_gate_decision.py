from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.enterprise.release_gate_aggregator import (
    EnterpriseReleaseGateInputs,
    build_enterprise_release_gate_inputs,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    EnterpriseReleaseGatePolicy,
    build_enterprise_release_gate_policy,
)


class EnterpriseReleaseGateDecision(TypedDict):
    decision_id: str
    profile_name: str
    status: str
    recommended_action: str
    blocking_checks: list[str]
    reason_codes: list[str]
    confidence: float


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _decision_confidence(*, status: str, pass_rate: float, average_score: float) -> float:
    raw = (float(pass_rate) * 0.5) + (float(average_score) * 0.5)
    if status == "fail":
        raw *= 0.5
    elif status == "warn":
        raw *= 0.8
    return _normalize_float_01(raw, default=0.0)


def decide_enterprise_release_gate(
    *,
    inputs: EnterpriseReleaseGateInputs,
    policy: EnterpriseReleaseGatePolicy,
    decision_id: object = "enterprise_release_gate:runtime",
) -> EnterpriseReleaseGateDecision:
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
    normalized_inputs = build_enterprise_release_gate_inputs(
        diagnostics={
            "verify": {"status": dict(inputs.get("release_checks", {})).get("verify", "missing")},
            "self_check": {"status": dict(inputs.get("release_checks", {})).get("self_check", "missing")},
            "reasoning_benchmark": {
                "summary": dict(inputs.get("benchmark_summary", {})),
            },
            "coverage": {
                "line_rate": inputs.get("coverage_ratio", None),
            },
            "reasoning_optimization": {
                "decision": dict(inputs.get("optimization_decision", {})),
            },
        },
        warnings=list(inputs.get("warnings", [])),
        profile_name=inputs.get("profile_name", "default"),
    )

    eval_required = dict(normalized_inputs.get("required_checks_evaluation") or {})
    benchmark = dict(normalized_inputs.get("benchmark_summary") or {})
    optimization = dict(normalized_inputs.get("optimization_decision") or {})

    reasons: list[str] = []
    blocking_checks = [str(x) for x in list(eval_required.get("failed_checks") or [])]
    has_failures = False

    if blocking_checks:
        has_failures = True
        reasons.append("required_checks_failed")

    total_cases = int(benchmark.get("total_cases", 0) or 0)
    pass_rate = float(benchmark.get("pass_rate", 0.0) or 0.0)
    average_score = float(benchmark.get("average_score", 0.0) or 0.0)
    coverage_ratio = normalized_inputs.get("coverage_ratio", None)
    if bool(normalized_policy.get("require_benchmark_summary", True)) and total_cases <= 0:
        has_failures = True
        reasons.append("benchmark_summary_missing")
    if pass_rate < float(normalized_policy.get("minimum_pass_rate", 0.0) or 0.0):
        has_failures = True
        reasons.append("benchmark_pass_rate_below_threshold")
    if average_score < float(normalized_policy.get("minimum_average_score", 0.0) or 0.0):
        has_failures = True
        reasons.append("benchmark_average_score_below_threshold")
    minimum_coverage_ratio = float(normalized_policy.get("minimum_coverage_ratio", 0.0) or 0.0)
    if minimum_coverage_ratio > 0.0:
        if coverage_ratio is None:
            has_failures = True
            reasons.append("coverage_summary_missing")
        elif float(coverage_ratio) < minimum_coverage_ratio:
            has_failures = True
            reasons.append("coverage_ratio_below_threshold")

    optimization_action = str(optimization.get("action", "defer") or "defer")
    if optimization_action == "reject":
        has_failures = True
        reasons.append("optimization_rejected")

    has_warnings = False
    if bool(eval_required.get("unstable_checks")):
        has_warnings = True
        reasons.append("required_checks_unstable")
    if int(normalized_inputs.get("warnings_count", 0) or 0) > 0:
        has_warnings = True
        reasons.append("warnings_present")
    if bool(normalized_policy.get("require_optimization_review", True)) and bool(
        optimization.get("requires_human_review", False)
    ):
        has_warnings = True
        reasons.append("optimization_review_required")

    if has_failures:
        status = "fail"
        recommended_action = "block"
    elif has_warnings and not bool(normalized_policy.get("allow_skipped", False)):
        status = "warn"
        recommended_action = "hold"
    else:
        status = "pass"
        recommended_action = "promote"
        reasons.append("release_gate_passed")

    return {
        "decision_id": _normalize_string(decision_id) or "enterprise_release_gate:runtime",
        "profile_name": str(normalized_policy.get("profile_name", "default") or "default"),
        "status": status,
        "recommended_action": recommended_action,
        "blocking_checks": sorted(set(blocking_checks)),
        "reason_codes": sorted(set(reasons)),
        "confidence": _decision_confidence(
            status=status,
            pass_rate=pass_rate,
            average_score=average_score,
        ),
    }
