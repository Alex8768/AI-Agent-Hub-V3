from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable

from src.layers.pro.reasoning.observability.timeline_model import (
    ReasoningTimeline,
    build_reasoning_timeline,
    build_reasoning_timeline_event,
)


def monotonic_now_ms() -> int:
    """Monotonic clock in milliseconds for duration measurement."""
    return int(perf_counter() * 1000)


@dataclass
class _ActiveEvent:
    event_type: str
    step_index: int
    started_at_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningTimelineCollector:
    """Collect timeline events via explicit start/end boundaries."""

    now_ms: Callable[[], int] = monotonic_now_ms
    _next_token: int = 1
    _active: dict[int, _ActiveEvent] = field(default_factory=dict)
    _events: list[dict[str, Any]] = field(default_factory=list)

    def start_event(
        self,
        *,
        event_type: str,
        step_index: int,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        token = int(self._next_token)
        self._next_token += 1
        self._active[token] = _ActiveEvent(
            event_type=str(event_type or "").strip(),
            step_index=int(step_index or 0),
            started_at_ms=int(self.now_ms()),
            metadata=dict(metadata or {}),
        )
        return token

    def end_event(
        self,
        *,
        token: int,
        status: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        active = self._active.pop(int(token), None)
        if active is None:
            return None
        ended_at_ms = int(self.now_ms())
        merged_metadata = dict(active.metadata or {})
        merged_metadata.update(dict(metadata or {}))
        event = build_reasoning_timeline_event(
            event_type=active.event_type,
            step_index=active.step_index,
            started_at_ms=active.started_at_ms,
            ended_at_ms=ended_at_ms,
            status=str(status or "").strip(),
            metadata=merged_metadata,
        )
        self._events.append(event)
        return dict(event)

    def to_timeline(self) -> ReasoningTimeline:
        return build_reasoning_timeline(events=list(self._events))


def collect_reasoning_timeline(*, events: list[dict[str, Any]]) -> ReasoningTimeline:
    """Build normalized timeline from externally provided event rows."""
    return build_reasoning_timeline(events=list(events or []))
