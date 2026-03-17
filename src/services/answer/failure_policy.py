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
    query = str(getattr(req, "query", "") or "").strip()
    is_substantive = len([t for t in query.replace("?", " ").split() if t.strip()]) >= 6

    diagnostics: dict[str, Any] = {
        "failure_policy": {
            "mode": "controlled_fallback",
            "reason_code": str(reason_code or "answer_runtime_controlled_fallback"),
            "error_type": type(error).__name__,
        }
    }
    diagnostics["quality_trace"] = [
        "quality_trace:controlled_fallback_applied",
        "quality_trace:llm_error_fallback",
    ]
    if route:
        diagnostics["runtime_mode"] = {
            "requested_mode": str(route.get("requested_mode", "answer") or "answer"),
            "selected_mode": str(route.get("selected_mode", "answer") or "answer"),
            "reason_codes": [str(x) for x in list(route.get("reason_codes") or []) if str(x)],
        }
    if is_substantive:
        answer = (
            "I could not complete the full runtime path due to a temporary model/runtime issue.\n\n"
            "What I can do safely right now:\n"
            "1) Provide a structured baseline plan for your request\n"
            "2) Refine it once you confirm constraints/context\n"
            "3) Retry source-grounded synthesis after runtime recovers"
        )
    else:
        answer = (
            "I hit a controlled runtime fallback while preparing the answer.\n"
            "Please retry, or provide a slightly more specific prompt and I will continue safely."
        )
    return AnswerResponse(
        answer=answer,
        confidence=0.0,
        request_id="",
        workspace_id=str(workspace_id or ""),
        warnings=[str(reason_code or "answer_runtime_controlled_fallback")],
        diagnostics=diagnostics,
    )
