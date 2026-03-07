from __future__ import annotations

from typing import Any, TypedDict


class ReasoningTimelineEvent(TypedDict):
    event_type: str
    step_index: int
    started_at_ms: int
    ended_at_ms: int
    duration_ms: int
    status: str
    metadata: dict[str, Any]


class ReasoningTimeline(TypedDict):
    events: list[ReasoningTimelineEvent]
    total_duration_ms: int


def _to_non_negative_int(value: object) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except Exception:
        return 0
    return max(0, number)


def build_reasoning_timeline_event(
    *,
    event_type: str,
    step_index: int,
    started_at_ms: int,
    ended_at_ms: int,
    duration_ms: int | None = None,
    status: str = "",
    metadata: dict[str, Any] | None = None,
) -> ReasoningTimelineEvent:
    """Build normalized timeline event with deterministic numeric fields."""
    started = _to_non_negative_int(started_at_ms)
    ended = max(started, _to_non_negative_int(ended_at_ms))
    resolved_duration = (
        ended - started
        if duration_ms is None
        else _to_non_negative_int(duration_ms)
    )
    return {
        "event_type": str(event_type or "").strip(),
        "step_index": _to_non_negative_int(step_index),
        "started_at_ms": started,
        "ended_at_ms": ended,
        "duration_ms": _to_non_negative_int(resolved_duration),
        "status": str(status or "").strip(),
        "metadata": dict(metadata or {}),
    }


def build_reasoning_timeline(*, events: list[dict[str, Any]]) -> ReasoningTimeline:
    """Build normalized reasoning timeline and aggregate duration."""
    normalized: list[ReasoningTimelineEvent] = []
    for raw in list(events or []):
        item = raw if isinstance(raw, dict) else {}
        normalized.append(
            build_reasoning_timeline_event(
                event_type=str(item.get("event_type", "") or ""),
                step_index=int(item.get("step_index", 0) or 0),
                started_at_ms=int(item.get("started_at_ms", 0) or 0),
                ended_at_ms=int(item.get("ended_at_ms", 0) or 0),
                duration_ms=(
                    None
                    if item.get("duration_ms", None) is None
                    else int(item.get("duration_ms", 0) or 0)
                ),
                status=str(item.get("status", "") or ""),
                metadata=dict(item.get("metadata", {}) or {}),
            )
        )
    return {
        "events": normalized,
        "total_duration_ms": int(sum(int(e.get("duration_ms", 0) or 0) for e in normalized)),
    }
