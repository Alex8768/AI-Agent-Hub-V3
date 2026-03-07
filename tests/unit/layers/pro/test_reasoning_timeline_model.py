from __future__ import annotations

from src.layers.pro.reasoning.observability.timeline_model import (
    build_reasoning_timeline,
    build_reasoning_timeline_event,
)


def test_build_reasoning_timeline_event_keeps_expected_shape():
    event = build_reasoning_timeline_event(
        event_type="planner",
        step_index=1,
        started_at_ms=100,
        ended_at_ms=112,
        status="pass",
        metadata={"decision": "continue"},
    )
    assert event == {
        "event_type": "planner",
        "step_index": 1,
        "started_at_ms": 100,
        "ended_at_ms": 112,
        "duration_ms": 12,
        "status": "pass",
        "metadata": {"decision": "continue"},
    }


def test_build_reasoning_timeline_event_normalizes_negative_and_blank_values():
    event = build_reasoning_timeline_event(
        event_type="  verify  ",
        step_index=-3,
        started_at_ms=-10,
        ended_at_ms=-5,
        duration_ms=-9,
        status="  warn  ",
        metadata=None,
    )
    assert event == {
        "event_type": "verify",
        "step_index": 0,
        "started_at_ms": 0,
        "ended_at_ms": 0,
        "duration_ms": 0,
        "status": "warn",
        "metadata": {},
    }


def test_build_reasoning_timeline_aggregates_duration_and_preserves_order():
    timeline = build_reasoning_timeline(
        events=[
            {
                "event_type": "planner",
                "step_index": 0,
                "started_at_ms": 10,
                "ended_at_ms": 25,
                "status": "pass",
                "metadata": {},
            },
            {
                "event_type": "verify",
                "step_index": 0,
                "started_at_ms": 25,
                "ended_at_ms": 29,
                "duration_ms": 3,
                "status": "warn",
                "metadata": {"reason": "low_coverage"},
            },
        ]
    )
    assert [e["event_type"] for e in timeline["events"]] == ["planner", "verify"]
    assert [e["duration_ms"] for e in timeline["events"]] == [15, 3]
    assert timeline["total_duration_ms"] == 18
