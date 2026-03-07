from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.trace.trace_model import ReasoningTrace, build_reasoning_trace


def enrich_reasoning_trace_with_timeline(
    *,
    trace: dict[str, Any],
    timeline: dict[str, Any],
) -> ReasoningTrace:
    """Attach normalized timeline to an existing reasoning trace payload."""
    payload = trace if isinstance(trace, dict) else {}
    return build_reasoning_trace(
        query=str(payload.get("query", "") or ""),
        plan=list(payload.get("plan") or []),
        steps=list(payload.get("steps") or []),
        verify_results=list(payload.get("verify_results") or []),
        quality=dict(payload.get("quality") or {}),
        timeline=dict(timeline or {}),
        answer=str(payload.get("answer", "") or ""),
    )
