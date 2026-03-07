from __future__ import annotations

import json
from typing import Any

from src.layers.pro.reasoning.trace.trace_model import ReasoningTrace, build_reasoning_trace


def _normalize_trace_payload(trace: dict[str, Any]) -> ReasoningTrace:
    payload = trace if isinstance(trace, dict) else {}
    return build_reasoning_trace(
        query=str(payload.get("query", "") or ""),
        plan=list(payload.get("plan") or []),
        steps=list(payload.get("steps") or []),
        verify_results=list(payload.get("verify_results") or []),
        quality=dict(payload.get("quality") or {}),
        answer=str(payload.get("answer", "") or ""),
    )


def serialize_reasoning_trace(*, trace: dict[str, Any]) -> str:
    """Serialize reasoning trace into stable JSON representation."""
    normalized = _normalize_trace_payload(trace)
    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def deserialize_reasoning_trace(*, payload: str) -> ReasoningTrace:
    """Deserialize JSON payload into normalized reasoning trace contract."""
    parsed = json.loads(str(payload or "{}"))
    if not isinstance(parsed, dict):
        raise ValueError("Reasoning trace payload must be a JSON object")
    return _normalize_trace_payload(parsed)
