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


def consolidate_enterprise_required_checks_matrix(
    *,
    policies: list[EnterpriseRequiredChecksPolicy] | None,
    workflow_required_checks_by_profile: dict[str, object] | None = None,
    blocking_checks_by_profile: dict[str, object] | None = None,
    version: object = "v1",
) -> EnterpriseRequiredChecksMatrix:
    """Merge policy checks with normalized workflow checks into one deterministic matrix."""
    normalized_policies: list[EnterpriseRequiredChecksPolicy] = []
    by_profile: dict[str, EnterpriseRequiredChecksPolicy] = {}
    workflow_map = dict(workflow_required_checks_by_profile or {})

    for raw_policy in list(policies or []):
        policy = build_enterprise_required_checks_policy(
            profile_name=raw_policy.get("profile_name", "default"),
            required_checks=raw_policy.get("required_checks", []),
            stable_statuses=raw_policy.get("stable_statuses", ["pass"]),
            treat_missing_as_failure=raw_policy.get("treat_missing_as_failure", True),
            allow_warnings=raw_policy.get("allow_warnings", False),
        )
        profile_name = str(policy.get("profile_name", "default") or "default")
        workflow_checks = _normalize_string_list(workflow_map.get(profile_name, []))
        merged_required = sorted(set(list(policy.get("required_checks", [])) + workflow_checks))
        merged = build_enterprise_required_checks_policy(
            profile_name=profile_name,
            required_checks=merged_required,
            stable_statuses=policy.get("stable_statuses", ["pass"]),
            treat_missing_as_failure=policy.get("treat_missing_as_failure", True),
            allow_warnings=policy.get("allow_warnings", False),
        )
        by_profile[profile_name] = merged

    for raw_profile_name, raw_checks in workflow_map.items():
        profile_name = _normalize_string(raw_profile_name) or "default"
        if profile_name in by_profile:
            continue
        by_profile[profile_name] = build_enterprise_required_checks_policy(
            profile_name=profile_name,
            required_checks=_normalize_string_list(raw_checks),
            stable_statuses=["pass"],
            treat_missing_as_failure=True,
            allow_warnings=False,
        )

    normalized_policies = [by_profile[name] for name in sorted(by_profile)]
    return build_enterprise_required_checks_matrix(
        policies=normalized_policies,
        blocking_checks_by_profile=blocking_checks_by_profile,
        version=version,
    )
