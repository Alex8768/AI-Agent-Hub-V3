from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    EnterpriseRequiredChecksPolicy,
    build_enterprise_required_checks_policy,
)


class EnterpriseRequiredChecksMatrixEntry(TypedDict):
    profile_name: str
    required_checks: list[str]
    blocking_checks: list[str]
    stable_statuses: list[str]
    treat_missing_as_failure: bool
    allow_warnings: bool


class EnterpriseRequiredChecksMatrix(TypedDict):
    version: str
    profiles: list[EnterpriseRequiredChecksMatrixEntry]
    all_required_checks: list[str]
    all_blocking_checks: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_enterprise_required_checks_matrix(
    *,
    policies: list[EnterpriseRequiredChecksPolicy] | None,
    blocking_checks_by_profile: dict[str, object] | None = None,
    version: object = "v1",
) -> EnterpriseRequiredChecksMatrix:
    normalized_profiles: list[EnterpriseRequiredChecksMatrixEntry] = []
    all_required_checks: list[str] = []
    all_blocking_checks: list[str] = []
    raw_blocks = dict(blocking_checks_by_profile or {})

    for raw_policy in list(policies or []):
        policy = build_enterprise_required_checks_policy(
            profile_name=raw_policy.get("profile_name", "default"),
            required_checks=raw_policy.get("required_checks", []),
            stable_statuses=raw_policy.get("stable_statuses", ["pass"]),
            treat_missing_as_failure=raw_policy.get("treat_missing_as_failure", True),
            allow_warnings=raw_policy.get("allow_warnings", False),
        )
        profile_name = str(policy.get("profile_name", "default") or "default")
        required_checks = list(policy.get("required_checks", []))
        blocking = _normalize_string_list(raw_blocks.get(profile_name, required_checks))
        entry: EnterpriseRequiredChecksMatrixEntry = {
            "profile_name": profile_name,
            "required_checks": required_checks,
            "blocking_checks": blocking,
            "stable_statuses": list(policy.get("stable_statuses", ["pass"])),
            "treat_missing_as_failure": bool(policy.get("treat_missing_as_failure", True)),
            "allow_warnings": bool(policy.get("allow_warnings", False)),
        }
        normalized_profiles.append(entry)
        all_required_checks.extend(required_checks)
        all_blocking_checks.extend(blocking)

    normalized_profiles = sorted(normalized_profiles, key=lambda item: item["profile_name"])
    return {
        "version": _normalize_string(version) or "v1",
        "profiles": normalized_profiles,
        "all_required_checks": sorted(set(all_required_checks)),
        "all_blocking_checks": sorted(set(all_blocking_checks)),
    }
