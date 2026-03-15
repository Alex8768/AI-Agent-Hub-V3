"""Failure policy seam for controlled answer fallback responses."""

from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.contracts import AnswerResponse


def build_controlled_answer_fallback(
    *,
    req: object,
    workspace_id: str,
    reason_code: str,
    error: Exception,
    route: dict[str, Any] | None = None,
) -> AnswerResponse:
    diagnostics: dict[str, Any] = {
        "failure_policy": {
            "mode": "controlled_fallback",
            "reason_code": str(reason_code or "answer_runtime_controlled_fallback"),
            "error_type": type(error).__name__,
        }
    }
    if route:
        diagnostics["runtime_mode"] = {
            "requested_mode": str(route.get("requested_mode", "answer") or "answer"),
            "selected_mode": str(route.get("selected_mode", "answer") or "answer"),
            "reason_codes": [str(x) for x in list(route.get("reason_codes") or []) if str(x)],
        }
    return AnswerResponse(
        answer="I hit a controlled runtime fallback while preparing the answer. Please retry or narrow the request.",
        confidence=0.0,
        request_id="",
        workspace_id=str(workspace_id or ""),
        warnings=[str(reason_code or "answer_runtime_controlled_fallback")],
        diagnostics=diagnostics,
    )
