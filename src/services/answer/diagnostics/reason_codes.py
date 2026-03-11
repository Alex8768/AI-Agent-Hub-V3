"""Diagnostics reason-code helpers extracted from answer service."""

from __future__ import annotations


def append_planning_reason_codes(
    *,
    diagnostics: dict[str, object],
    reason_codes: list[str],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    merged = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
    merged.extend(str(x) for x in list(reason_codes or []) if str(x or "").strip())
    diag["planning_reason_codes"] = sorted(set(merged))
    return diag
