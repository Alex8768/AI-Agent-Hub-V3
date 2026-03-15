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
    mode = str(filters.get("response_presentation", filters.get("diagnostics_view", "full")) or "full").lower()
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    if mode != "compact":
        diagnostics.setdefault("presentation", {"mode": "full", "excluded_diagnostics": []})
        setattr(resp, "diagnostics", diagnostics)
        return resp

    excluded = [k for k in _COMPACT_DIAGNOSTICS_EXCLUDE_KEYS if k in diagnostics]
    for key in excluded:
        diagnostics.pop(key, None)
    diagnostics["presentation"] = {"mode": "compact", "excluded_diagnostics": excluded}
    setattr(resp, "diagnostics", diagnostics)
    return resp
