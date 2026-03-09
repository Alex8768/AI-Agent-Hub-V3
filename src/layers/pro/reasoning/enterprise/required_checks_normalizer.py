from __future__ import annotations

import re


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_check_name(value: object) -> str:
    raw = _normalize_string(value).lower()
    if not raw:
        return ""
    normalized = re.sub(r"[\s\-]+", "_", raw)
    normalized = re.sub(r"[^a-z0-9_/:]", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_check_name(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def _flatten_string_tokens(value: str) -> list[str]:
    if "," in value:
        return [_normalize_string(token) for token in value.split(",")]
    return [_normalize_string(value)]


def _resolve_aliases(
    check_name: str,
    aliases: dict[str, object] | None,
) -> list[str]:
    if not aliases:
        return [check_name]
    key = _normalize_check_name(check_name)
    alias_value = aliases.get(key)
    if alias_value is None:
        return [check_name]
    return _normalize_required_checks_input(alias_value, aliases=aliases)


def _collect_from_jobs(jobs: dict[str, object], aliases: dict[str, object] | None) -> list[str]:
    checks: list[str] = []
    for job_id, payload in dict(jobs or {}).items():
        normalized_id = _normalize_check_name(job_id)
        if normalized_id:
            checks.extend(_resolve_aliases(normalized_id, aliases))
        if isinstance(payload, dict):
            name = _normalize_string(payload.get("name", ""))
            if name:
                tail = name.split("/")[-1]
                normalized_name = _normalize_check_name(tail)
                if normalized_name:
                    checks.extend(_resolve_aliases(normalized_name, aliases))
    return sorted(set(checks))


def _normalize_required_checks_input(
    payload: object,
    *,
    aliases: dict[str, object] | None,
) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, str):
        checks: list[str] = []
        for token in _flatten_string_tokens(payload):
            normalized = _normalize_check_name(token)
            if normalized:
                checks.extend(_resolve_aliases(normalized, aliases))
        return sorted(set(checks))
    if isinstance(payload, (list, tuple, set)):
        checks: list[str] = []
        for item in list(payload):
            checks.extend(_normalize_required_checks_input(item, aliases=aliases))
        return sorted(set(checks))
    if isinstance(payload, dict):
        checks: list[str] = []
        raw = dict(payload)
        checks.extend(_normalize_required_checks_input(raw.get("required_checks"), aliases=aliases))
        checks.extend(_normalize_required_checks_input(raw.get("checks"), aliases=aliases))
        checks.extend(_normalize_required_checks_input(raw.get("contexts"), aliases=aliases))
        required_status = raw.get("required_status_checks")
        if isinstance(required_status, dict):
            checks.extend(_normalize_required_checks_input(required_status.get("contexts"), aliases=aliases))
        jobs = raw.get("jobs")
        if isinstance(jobs, dict):
            checks.extend(_collect_from_jobs(jobs, aliases))
        return sorted(set(checks))
    return []


def normalize_enterprise_required_checks_by_profile(
    *,
    workflow_definitions: object,
    aliases: dict[str, object] | None = None,
    default_profile: object = "enterprise_default",
) -> dict[str, list[str]]:
    """Normalize required checks from mixed workflow definitions into profile mapping."""
    normalized_aliases = {
        _normalize_check_name(name): value for name, value in dict(aliases or {}).items() if _normalize_check_name(name)
    }
    profile_name = _normalize_string(default_profile) or "enterprise_default"
    if isinstance(workflow_definitions, dict):
        raw = dict(workflow_definitions)
        by_profile = raw.get("by_profile")
        if isinstance(by_profile, dict):
            result: dict[str, list[str]] = {}
            for raw_profile_name, payload in dict(by_profile).items():
                normalized_profile = _normalize_string(raw_profile_name) or profile_name
                checks = _normalize_required_checks_input(payload, aliases=normalized_aliases)
                result[normalized_profile] = checks
            return dict(sorted(result.items(), key=lambda item: item[0]))
    checks = _normalize_required_checks_input(workflow_definitions, aliases=normalized_aliases)
    return {profile_name: checks}
