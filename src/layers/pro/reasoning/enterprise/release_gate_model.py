from __future__ import annotations

from typing import TypedDict


class EnterpriseReleaseGatePolicy(TypedDict):
    profile_name: str
    required_checks: list[str]
    blocking_checks: list[str]
    minimum_pass_rate: float
    minimum_average_score: float
    minimum_coverage_ratio: float
    allow_skipped: bool
    require_benchmark_summary: bool
    require_optimization_review: bool
    allowed_warning_codes: list[str]


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


def build_enterprise_release_gate_policy(
    *,
    profile_name: object = "default",
    required_checks: object = None,
    blocking_checks: object = None,
    minimum_pass_rate: object = 0.9,
    minimum_average_score: object = 0.8,
    minimum_coverage_ratio: object = 0.0,
    allow_skipped: object = False,
    require_benchmark_summary: object = True,
    require_optimization_review: object = True,
    allowed_warning_codes: object = None,
) -> EnterpriseReleaseGatePolicy:
    """Build normalized enterprise release-gate policy contract."""
    normalized_required_checks = _normalize_string_list(required_checks)
    normalized_blocking_checks = _normalize_string_list(blocking_checks)
    if not normalized_blocking_checks:
        normalized_blocking_checks = list(normalized_required_checks)
    return {
        "profile_name": _normalize_string(profile_name),
        "required_checks": normalized_required_checks,
        "blocking_checks": normalized_blocking_checks,
        "minimum_pass_rate": _normalize_float_01(minimum_pass_rate, default=0.9),
        "minimum_average_score": _normalize_float_01(minimum_average_score, default=0.8),
        "minimum_coverage_ratio": _normalize_float_01(minimum_coverage_ratio, default=0.0),
        "allow_skipped": bool(allow_skipped),
        "require_benchmark_summary": bool(require_benchmark_summary),
        "require_optimization_review": bool(require_optimization_review),
        "allowed_warning_codes": _normalize_string_list(allowed_warning_codes),
    }


def build_enterprise_release_gate_policy_from_dict(
    payload: dict[str, object] | None,
) -> EnterpriseReleaseGatePolicy:
    raw = payload if isinstance(payload, dict) else {}
    return build_enterprise_release_gate_policy(
        profile_name=raw.get("profile_name", "default"),
        required_checks=raw.get("required_checks", []),
        blocking_checks=raw.get("blocking_checks", []),
        minimum_pass_rate=raw.get("minimum_pass_rate", 0.9),
        minimum_average_score=raw.get("minimum_average_score", 0.8),
        minimum_coverage_ratio=raw.get("minimum_coverage_ratio", 0.0),
        allow_skipped=raw.get("allow_skipped", False),
        require_benchmark_summary=raw.get("require_benchmark_summary", True),
        require_optimization_review=raw.get("require_optimization_review", True),
        allowed_warning_codes=raw.get("allowed_warning_codes", []),
    )
