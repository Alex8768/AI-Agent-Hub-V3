from __future__ import annotations

from src.layers.pro.reasoning.observability.timeline_collector import ReasoningTimelineCollector
from src.layers.pro.reasoning.trace.trace_collector import collect_reasoning_trace
from src.layers.pro.reasoning.trace.trace_serializer import deserialize_reasoning_trace, serialize_reasoning_trace


class _Clock:
    def __init__(self, values: list[int]):
        self._values = list(values)

    def __call__(self) -> int:
        if not self._values:
            return 0
        return int(self._values.pop(0))


def test_reasoning_timeline_event_ordering_is_stable():
    collector = ReasoningTimelineCollector(now_ms=_Clock([100, 112, 112, 120, 120, 128]))
    p = collector.start_event(event_type="planner", step_index=0)
    collector.end_event(token=p, status="pass")
    r = collector.start_event(event_type="reason", step_index=0)
    collector.end_event(token=r, status="pass")
    v = collector.start_event(event_type="verify", step_index=0)
    collector.end_event(token=v, status="warn")

    timeline = collector.to_timeline()
    assert [e["event_type"] for e in timeline["events"]] == ["planner", "reason", "verify"]


def test_reasoning_timeline_duration_calculation_is_consistent():
    collector = ReasoningTimelineCollector(now_ms=_Clock([10, 25, 25, 31]))
    t1 = collector.start_event(event_type="planner", step_index=0)
    collector.end_event(token=t1, status="pass")
    t2 = collector.start_event(event_type="verify", step_index=0)
    collector.end_event(token=t2, status="pass")

    timeline = collector.to_timeline()
    assert [e["duration_ms"] for e in timeline["events"]] == [15, 6]
    assert timeline["total_duration_ms"] == 21


def test_reasoning_timeline_trace_integration_roundtrip():
    collector = ReasoningTimelineCollector(now_ms=_Clock([1, 4]))
    token = collector.start_event(event_type="planner", step_index=0)
    collector.end_event(token=token, status="pass")
    timeline = collector.to_timeline()

    trace = collect_reasoning_trace(
        query="Q",
        plan={"steps": [{"description": "step-1"}]},
        step_results=[
            {
                "step_index": 0,
                "step_description": "step-1",
                "reasoning_output": "out-1",
                "verify_status": "pass",
                "verify_reasons": [],
            }
        ],
        quality={"confidence": 0.9},
        timeline=timeline,
        answer="A",
    )

    payload = serialize_reasoning_trace(trace=trace)
    restored = deserialize_reasoning_trace(payload=payload)
    assert restored["timeline"] == timeline
    assert restored["query"] == "Q"
