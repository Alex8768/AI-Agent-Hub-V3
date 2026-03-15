"""Runtime policy profile resolution seam for answer action governance."""

from __future__ import annotations


_PROFILE_NAMES: tuple[str, ...] = ("prod_strict", "dev_guided", "dev_full")


def resolve_runtime_policy_profile(*, req: object, settings: object) -> dict[str, object]:
    profile = "dev_guided" if bool(getattr(settings, "debug", False)) else "prod_strict"
    source = "defaults"
    reason_codes: list[str] = []

    filters = dict(getattr(req, "filters", None) or {})
    requested = str(filters.get("runtime_policy_profile", "") or "").strip().lower()
    if requested:
        if requested not in _PROFILE_NAMES:
            reason_codes.append("runtime_policy_profile_invalid_ignored")
        elif not bool(getattr(settings, "debug", False)):
            reason_codes.append("runtime_policy_profile_override_blocked_in_non_debug")
        else:
            profile = requested
            source = "request_override"
            reason_codes.append("runtime_policy_profile_override_applied")

    allow_act_read_only = profile in {"dev_guided", "dev_full"}
    return {
        "profile_name": profile,
        "source": source,
        "allow_act_read_only": allow_act_read_only,
        "reason_codes": reason_codes,
    }
