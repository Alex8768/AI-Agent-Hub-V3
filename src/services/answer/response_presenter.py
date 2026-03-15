"""Response presenter seam for compact/full diagnostics shaping."""

from __future__ import annotations

from typing import Any


_COMPACT_DIAGNOSTICS_EXCLUDE_KEYS: tuple[str, ...] = (
    "planner_runtime_parity",
    "feedback_learning",
    "feedback_adaptation",
    "tool_selection",
    "assistant_recovery",
)


def present_answer_response(*, req: object, resp: object) -> object:
    filters = dict(getattr(req, "filters", None) or {})
    requested_mode = str(filters.get("diagnostics_view", filters.get("response_presentation", "full")) or "full").lower()
    mode_aliases = {"expanded": "full"}
    mode = mode_aliases.get(requested_mode, requested_mode)
    reason_codes: list[str] = []
    if requested_mode in mode_aliases:
        reason_codes.append("diagnostics_view_alias_expanded_to_full")
    if mode not in {"full", "compact"}:
        mode = "full"
        reason_codes.append("diagnostics_view_invalid_fallback_full")
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    if mode != "compact":
        diagnostics["presentation"] = {
            "mode": "full",
            "requested_mode": requested_mode,
            "resolved_mode": mode,
            "excluded_diagnostics": [],
            "reason_codes": reason_codes,
        }
        setattr(resp, "diagnostics", diagnostics)
        return resp

    excluded = [k for k in _COMPACT_DIAGNOSTICS_EXCLUDE_KEYS if k in diagnostics]
    for key in excluded:
        diagnostics.pop(key, None)
    diagnostics["presentation"] = {
        "mode": "compact",
        "requested_mode": requested_mode,
        "resolved_mode": mode,
        "excluded_diagnostics": excluded,
        "reason_codes": reason_codes,
    }
    setattr(resp, "diagnostics", diagnostics)
    return resp
