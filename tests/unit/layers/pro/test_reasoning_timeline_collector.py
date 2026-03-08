from __future__ import annotations

from src.layers.pro.reasoning.observability.timeline_collector import (
    ReasoningTimelineCollector,
    collect_reasoning_timeline,
)


class _FakeClock:
    def __init__(self, values: list[int]):
        self._values = list(values)

    def __call__(self) -> int:
        if not self._values:
            return 0
        return int(self._values.pop(0))


def test_reasoning_timeline_collector_records_duration_with_start_end():
    collector = ReasoningTimelineCollector(now_ms=_FakeClock([100, 112]))
    token = collector.start_event(event_type="planner", step_index=0, metadata={"a": 1})
    event = collector.end_event(token=token, status="pass", metadata={"b": 2})
    assert event == {
        "event_type": "planner",
        "step_index": 0,
        "started_at_ms": 100,
        "ended_at_ms": 112,
        "duration_ms": 12,
        "status": "pass",
        "metadata": {"a": 1, "b": 2},
    }
    timeline = collector.to_timeline()
    assert timeline["total_duration_ms"] == 12
    assert len(timeline["events"]) == 1


def test_reasoning_timeline_collector_preserves_event_order():
    collector = ReasoningTimelineCollector(now_ms=_FakeClock([10, 20, 20, 29]))
    t1 = collector.start_event(event_type="planner", step_index=0)
    collector.end_event(token=t1, status="pass")
    t2 = collector.start_event(event_type="verify", step_index=0)
    collector.end_event(token=t2, status="warn")
    timeline = collector.to_timeline()
    assert [e["event_type"] for e in timeline["events"]] == ["planner", "verify"]
    assert [e["duration_ms"] for e in timeline["events"]] == [10, 9]
    assert timeline["total_duration_ms"] == 19


def test_reasoning_timeline_collector_unknown_token_is_safe_noop():
    collector = ReasoningTimelineCollector(now_ms=_FakeClock([100]))
    assert collector.end_event(token=999, status="pass") is None
    assert collector.to_timeline() == {"events": [], "total_duration_ms": 0}


def test_collect_reasoning_timeline_normalizes_external_rows():
    timeline = collect_reasoning_timeline(
        events=[
            {
                "event_type": " planner ",
                "step_index": -1,
                "started_at_ms": 100,
                "ended_at_ms": 90,
                "status": " pass ",
                "metadata": {"x": 1},
            }
        ]
    )
    assert timeline == {
        "events": [
            {
                "event_type": "planner",
                "step_index": 0,
                "started_at_ms": 100,
                "ended_at_ms": 100,
                "duration_ms": 0,
                "status": "pass",
                "metadata": {"x": 1},
            }
        ],
        "total_duration_ms": 0,
    }
