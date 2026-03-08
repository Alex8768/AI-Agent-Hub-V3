from __future__ import annotations

from typing import Any, TypedDict

from src.layers.pro.reasoning.observability.timeline_model import (
    ReasoningTimeline,
    build_reasoning_timeline,
)


class ReasoningTraceVerifyResult(TypedDict):
    status: str
    reasons: list[str]


class ReasoningTrace(TypedDict):
    query: str
    plan: list[str]
    steps: list[str]
    verify_results: list[ReasoningTraceVerifyResult]
    quality: dict[str, Any]
    timeline: ReasoningTimeline
    answer: str


def _normalize_string_list(items: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in items:
        value = str(raw or "").strip()
        if not value:
            continue
        normalized.append(value)
    return normalized


def _normalize_verify_results(
    verify_results: list[dict[str, Any]],
) -> list[ReasoningTraceVerifyResult]:
    normalized: list[ReasoningTraceVerifyResult] = []
    for raw in verify_results:
        item = raw if isinstance(raw, dict) else {}
        status = str(item.get("status", "") or "").strip()
        reasons_raw = item.get("reasons", [])
        reasons_list = reasons_raw if isinstance(reasons_raw, list) else [reasons_raw]
        reasons = _normalize_string_list([str(v or "") for v in reasons_list])
        normalized.append(
            {
                "status": status,
                "reasons": reasons,
            }
        )
    return normalized


def build_reasoning_trace(
    *,
    query: str,
    plan: list[str],
    steps: list[str],
    verify_results: list[dict[str, Any]],
    quality: dict[str, Any],
    timeline: dict[str, Any] | None = None,
    answer: str,
) -> ReasoningTrace:
    """Build normalized reasoning trace with deterministic shape."""
    timeline_raw = timeline if isinstance(timeline, dict) else {}
    normalized_timeline = build_reasoning_timeline(
        events=list(timeline_raw.get("events") or []),
    )
    return {
        "query": str(query or "").strip(),
        "plan": _normalize_string_list(plan),
        "steps": _normalize_string_list(steps),
        "verify_results": _normalize_verify_results(verify_results),
        "quality": dict(quality or {}),
        "timeline": normalized_timeline,
        "answer": str(answer or "").strip(),
    }
