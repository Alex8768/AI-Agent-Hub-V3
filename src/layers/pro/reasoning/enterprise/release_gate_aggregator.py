from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.enterprise.coverage_contract import (
    resolve_coverage_ratio_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    EnterpriseRequiredChecksEvaluation,
    EnterpriseRequiredChecksPolicy,
    build_enterprise_required_checks_policy,
    evaluate_enterprise_required_checks,
)

ALLOWED_CHECK_STATUSES = {"pass", "warn", "fail", "missing"}
ALLOWED_OPTIMIZATION_ACTIONS = {"approve", "defer", "reject"}


class EnterpriseReleaseGateBenchmarkSummary(TypedDict):
    suite_name: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_score: float


class EnterpriseReleaseGateOptimizationDecision(TypedDict):
    action: str
    requires_human_review: bool


class EnterpriseReleaseGateInputs(TypedDict):
    profile_name: str
    release_checks: dict[str, str]
    benchmark_summary: EnterpriseReleaseGateBenchmarkSummary
    coverage_ratio: float | None
    optimization_decision: EnterpriseReleaseGateOptimizationDecision
    warnings: list[str]
    warnings_count: int
    required_checks_evaluation: EnterpriseRequiredChecksEvaluation


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_int(value: object, *, default: int = 0, min_value: int = 0, max_value: int = 1_000_000) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


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


def _normalize_check_status(value: object) -> str:
    status = _normalize_string(value).lower()
    if status in ALLOWED_CHECK_STATUSES:
        return status
    return "missing"


def _normalize_optimization_action(value: object) -> str:
    action = _normalize_string(value).lower()
    if action in ALLOWED_OPTIMIZATION_ACTIONS:
        return action
    return "defer"


def build_enterprise_release_gate_inputs(
    *,
    diagnostics: dict[str, object] | None,
    warnings: list[object] | None = None,
    profile_name: object = "default",
    required_checks_policy: EnterpriseRequiredChecksPolicy | None = None,
) -> EnterpriseReleaseGateInputs:
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    verify = dict(diag.get("verify") or {})
    self_check = dict(diag.get("self_check") or {})
    benchmark = dict(diag.get("reasoning_benchmark") or {})
    benchmark_summary = dict(benchmark.get("summary") or {})
    optimization = dict(diag.get("reasoning_optimization") or {})
    optimization_decision = dict(optimization.get("decision") or {})

    release_checks = {
        "verify": _normalize_check_status(verify.get("status", "missing")),
        "self_check": _normalize_check_status(self_check.get("status", "missing")),
        "reasoning_benchmark": "pass" if isinstance(benchmark, dict) and bool(benchmark) else "missing",
        "reasoning_optimization": "pass" if isinstance(optimization, dict) and bool(optimization) else "missing",
    }
    release_checks = dict(sorted(release_checks.items(), key=lambda item: item[0]))

    normalized_profile = _normalize_string(profile_name) or "default"
    policy = (
        required_checks_policy
        if isinstance(required_checks_policy, dict)
        else build_enterprise_required_checks_policy(
            profile_name=normalized_profile,
            required_checks=list(release_checks.keys()),
            stable_statuses=["pass"],
            treat_missing_as_failure=True,
            allow_warnings=False,
        )
    )
    evaluation = evaluate_enterprise_required_checks(policy=policy, check_states=release_checks)

    normalized_warnings = _normalize_string_list(warnings)
    return {
        "profile_name": normalized_profile,
        "release_checks": release_checks,
        "benchmark_summary": {
            "suite_name": _normalize_string(benchmark_summary.get("suite_name", "")),
            "total_cases": _normalize_int(benchmark_summary.get("total_cases", 0), default=0, min_value=0),
            "passed_cases": _normalize_int(benchmark_summary.get("passed_cases", 0), default=0, min_value=0),
            "pass_rate": _normalize_float_01(benchmark_summary.get("pass_rate", 0.0), default=0.0),
            "average_score": _normalize_float_01(benchmark_summary.get("average_score", 0.0), default=0.0),
        },
        "coverage_ratio": resolve_coverage_ratio_from_diagnostics(diag),
        "optimization_decision": {
            "action": _normalize_optimization_action(optimization_decision.get("action", "defer")),
            "requires_human_review": bool(optimization_decision.get("requires_human_review", False)),
        },
        "warnings": normalized_warnings,
        "warnings_count": int(len(normalized_warnings)),
        "required_checks_evaluation": evaluation,
    }
