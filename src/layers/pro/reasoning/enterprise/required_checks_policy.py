from __future__ import annotations

from typing import TypedDict

DEFAULT_STABLE_STATUSES = ["pass"]
ALLOWED_CHECK_STATUSES = {"pass", "warn", "fail", "missing"}


class EnterpriseRequiredChecksPolicy(TypedDict):
    profile_name: str
    required_checks: list[str]
    stable_statuses: list[str]
    treat_missing_as_failure: bool
    allow_warnings: bool


class EnterpriseRequiredChecksEvaluation(TypedDict):
    profile_name: str
    passed: bool
    failed_checks: list[str]
    unstable_checks: list[str]
    missing_checks: list[str]
    reason_codes: list[str]
    check_states: dict[str, str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def _normalize_status(value: object) -> str:
    status = _normalize_string(value).lower()
    if status in ALLOWED_CHECK_STATUSES:
        return status
    return "missing"


def build_enterprise_required_checks_policy(
    *,
    profile_name: object = "default",
    required_checks: object = None,
    stable_statuses: object = None,
    treat_missing_as_failure: object = True,
    allow_warnings: object = False,
) -> EnterpriseRequiredChecksPolicy:
    normalized_stable = [
        status
        for status in _normalize_string_list(stable_statuses or DEFAULT_STABLE_STATUSES)
        if _normalize_status(status) != "missing"
    ]
    if not normalized_stable:
        normalized_stable = list(DEFAULT_STABLE_STATUSES)
    return {
        "profile_name": _normalize_string(profile_name) or "default",
        "required_checks": _normalize_string_list(required_checks),
        "stable_statuses": sorted(set(_normalize_status(x) for x in normalized_stable)),
        "treat_missing_as_failure": bool(treat_missing_as_failure),
        "allow_warnings": bool(allow_warnings),
    }


def evaluate_enterprise_required_checks(
    *,
    policy: EnterpriseRequiredChecksPolicy,
    check_states: dict[str, object] | None,
) -> EnterpriseRequiredChecksEvaluation:
    normalized_policy = build_enterprise_required_checks_policy(
        profile_name=policy.get("profile_name", "default"),
        required_checks=policy.get("required_checks", []),
        stable_statuses=policy.get("stable_statuses", DEFAULT_STABLE_STATUSES),
        treat_missing_as_failure=policy.get("treat_missing_as_failure", True),
        allow_warnings=policy.get("allow_warnings", False),
    )
    raw_states = dict(check_states or {})
    normalized_states = {str(name): _normalize_status(raw_states.get(name, "missing")) for name in raw_states}

    required_checks = list(normalized_policy.get("required_checks", []))
    stable = set(str(x) for x in list(normalized_policy.get("stable_statuses", [])))

    failed_checks: list[str] = []
    unstable_checks: list[str] = []
    missing_checks: list[str] = []
    reasons: list[str] = []

    for check_name in required_checks:
        status = _normalize_status(raw_states.get(check_name, "missing"))
        normalized_states[check_name] = status
        if status == "missing":
            missing_checks.append(check_name)
            if bool(normalized_policy.get("treat_missing_as_failure", True)):
                failed_checks.append(check_name)
                reasons.append("required_check_missing")
            continue
        if status == "warn" and bool(normalized_policy.get("allow_warnings", False)):
            unstable_checks.append(check_name)
            reasons.append("warning_status_present")
            continue
        if status not in stable:
            failed_checks.append(check_name)
            reasons.append("required_check_not_stable")

    return {
        "profile_name": str(normalized_policy.get("profile_name", "default")),
        "passed": len(failed_checks) == 0,
        "failed_checks": sorted(set(failed_checks)),
        "unstable_checks": sorted(set(unstable_checks)),
        "missing_checks": sorted(set(missing_checks)),
        "reason_codes": sorted(set(reasons)),
        "check_states": dict(sorted(normalized_states.items(), key=lambda item: item[0])),
    }
