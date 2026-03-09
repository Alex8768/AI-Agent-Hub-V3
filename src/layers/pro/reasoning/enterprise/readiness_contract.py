from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.enterprise.coverage_contract import (
    resolve_coverage_ratio_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    EnterpriseReleaseGatePolicy,
    build_enterprise_release_gate_policy,
)


class EnterpriseReadinessContract(TypedDict):
    profile_name: str
    release_gate_passed: bool
    failed_checks: list[str]
    benchmark_pass_rate: float
    benchmark_average_score: float
    optimization_action: str
    optimization_requires_review: bool
    warnings_count: int
    readiness_score: float
    reason_codes: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_int(value: object, *, default: int = 0, min_value: int = 0, max_value: int = 1_000_000) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def _normalize_optimization_action(value: object) -> str:
    action = _normalize_string(value).lower()
    if action not in {"approve", "defer", "reject"}:
        return "defer"
    return action


def build_enterprise_readiness_contract(
    *,
    profile_name: object,
    release_gate_passed: object,
    failed_checks: object,
    benchmark_pass_rate: object,
    benchmark_average_score: object,
    optimization_action: object,
    optimization_requires_review: object,
    warnings_count: object,
    reason_codes: object = None,
) -> EnterpriseReadinessContract:
    """Build normalized enterprise readiness contract."""
    pass_rate = _normalize_float_01(benchmark_pass_rate, default=0.0)
    average_score = _normalize_float_01(benchmark_average_score, default=0.0)
    warnings = _normalize_int(warnings_count, default=0, min_value=0)
    readiness_score = max(0.0, min(1.0, (pass_rate * 0.5) + (average_score * 0.4) - (warnings * 0.05)))
    return {
        "profile_name": _normalize_string(profile_name),
        "release_gate_passed": bool(release_gate_passed),
        "failed_checks": _normalize_string_list(failed_checks),
        "benchmark_pass_rate": pass_rate,
        "benchmark_average_score": average_score,
        "optimization_action": _normalize_optimization_action(optimization_action),
        "optimization_requires_review": bool(optimization_requires_review),
        "warnings_count": warnings,
        "readiness_score": readiness_score,
        "reason_codes": _normalize_string_list(reason_codes),
    }


def build_enterprise_readiness_contract_from_diagnostics(
    *,
    diagnostics: dict[str, object] | None,
    policy: EnterpriseReleaseGatePolicy | None = None,
    warnings: list[str] | None = None,
) -> EnterpriseReadinessContract:
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    gate_policy = (
        policy
        if isinstance(policy, dict)
        else build_enterprise_release_gate_policy(profile_name="default")
    )
    benchmark = dict(diag.get("reasoning_benchmark") or {})
    summary = dict(benchmark.get("summary") or {})
    optimization = dict(diag.get("reasoning_optimization") or {})
    optimization_decision = dict(optimization.get("decision") or {})
    checks_state = dict(diag.get("release_checks") or {})
    failed_checks = [
        name
        for name in list(gate_policy.get("blocking_checks") or [])
        if str(checks_state.get(name, "missing") or "missing") != "pass"
    ]
    pass_rate = _normalize_float_01(summary.get("pass_rate", 0.0), default=0.0)
    average_score = _normalize_float_01(summary.get("average_score", 0.0), default=0.0)
    coverage_ratio = resolve_coverage_ratio_from_diagnostics(diag)
    minimum_coverage_ratio = float(gate_policy.get("minimum_coverage_ratio", 0.0) or 0.0)
    release_gate_passed = (
        len(failed_checks) == 0
        and pass_rate >= float(gate_policy.get("minimum_pass_rate", 0.0) or 0.0)
        and average_score >= float(gate_policy.get("minimum_average_score", 0.0) or 0.0)
        and (
            minimum_coverage_ratio <= 0.0
            or (coverage_ratio is not None and float(coverage_ratio) >= minimum_coverage_ratio)
        )
    )
    reasons: list[str] = []
    if failed_checks:
        reasons.append("blocking_checks_failed")
    if pass_rate < float(gate_policy.get("minimum_pass_rate", 0.0) or 0.0):
        reasons.append("benchmark_pass_rate_below_threshold")
    if average_score < float(gate_policy.get("minimum_average_score", 0.0) or 0.0):
        reasons.append("benchmark_average_score_below_threshold")
    if minimum_coverage_ratio > 0.0:
        if coverage_ratio is None:
            reasons.append("coverage_summary_missing")
        elif float(coverage_ratio) < minimum_coverage_ratio:
            reasons.append("coverage_ratio_below_threshold")
    if bool(optimization_decision.get("requires_human_review", False)):
        reasons.append("optimization_requires_review")
    if str(optimization_decision.get("action", "") or "") == "reject":
        reasons.append("optimization_rejected")
    return build_enterprise_readiness_contract(
        profile_name=gate_policy.get("profile_name", "default"),
        release_gate_passed=release_gate_passed,
        failed_checks=failed_checks,
        benchmark_pass_rate=pass_rate,
        benchmark_average_score=average_score,
        optimization_action=optimization_decision.get("action", "defer"),
        optimization_requires_review=optimization_decision.get("requires_human_review", False),
        warnings_count=int(len(list(warnings or []))),
        reason_codes=reasons,
    )
