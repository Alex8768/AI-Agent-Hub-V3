"""Runtime mode routing seam for answer facade stabilization."""

from __future__ import annotations

from typing import Any


_SUPPORTED_RUNTIME_MODES: tuple[str, ...] = ("answer", "act")


def resolve_answer_runtime_mode(*, req: object, runtime_context: dict[str, object]) -> dict[str, Any]:
    filters = dict(getattr(req, "filters", None) or {})
    requested = str(filters.get("runtime_mode", filters.get("mode", "answer")) or "answer").strip().lower()
    if requested not in _SUPPORTED_RUNTIME_MODES:
        return {
            "requested_mode": requested or "answer",
            "selected_mode": "answer",
            "reason_codes": ["runtime_mode_unsupported_fallback_answer"],
        }
    if requested == "act" and not bool(runtime_context.get("assistant_actions_enabled", False)):
        return {
            "requested_mode": "act",
            "selected_mode": "answer",
            "reason_codes": ["runtime_mode_act_disabled_fallback_answer"],
        }
    return {
        "requested_mode": requested,
        "selected_mode": requested,
        "reason_codes": [],
    }


def apply_runtime_mode_diagnostics(*, resp: object, route: dict[str, Any]) -> None:
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    diagnostics["runtime_mode"] = {
        "requested_mode": str(route.get("requested_mode", "answer") or "answer"),
        "selected_mode": str(route.get("selected_mode", "answer") or "answer"),
        "reason_codes": [str(x) for x in list(route.get("reason_codes") or []) if str(x)],
    }
    setattr(resp, "diagnostics", diagnostics)
