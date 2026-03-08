from __future__ import annotations

from src.layers.pro.reasoning.trace.replay import (
    replay_reasoning_trace,
    replay_reasoning_trace_payload,
)
from src.layers.pro.reasoning.trace.trace_serializer import serialize_reasoning_trace


def test_replay_reasoning_trace_roundtrip_reproduces_normalized_trace():
    trace = {
        "query": "  Q  ",
        "plan": ["  s1  ", " ", "s2"],
        "steps": [" out1 ", "", "out2"],
        "verify_results": [
            {"status": " pass ", "reasons": ["  r1  ", " "]},
            {"status": "warn", "reasons": ["needs_support"]},
        ],
        "quality": {"coverage": 0.9},
        "timeline": {"events": [{"event_type": "planner", "step_index": 0, "started_at_ms": 5, "ended_at_ms": 9}]},
        "answer": "  A  ",
    }
    replayed = replay_reasoning_trace(trace=trace)
    assert replayed == {
        "query": "Q",
        "plan": ["s1", "s2"],
        "steps": ["out1", "out2"],
        "verify_results": [
            {"status": "pass", "reasons": ["r1"]},
            {"status": "warn", "reasons": ["needs_support"]},
        ],
        "quality": {"coverage": 0.9},
        "timeline": {
            "events": [
                {
                    "event_type": "planner",
                    "step_index": 0,
                    "started_at_ms": 5,
                    "ended_at_ms": 9,
                    "duration_ms": 4,
                    "status": "",
                    "metadata": {},
                }
            ],
            "total_duration_ms": 4,
        },
        "answer": "A",
    }


def test_replay_reasoning_trace_is_deterministic_across_runs():
    trace = {
        "query": "Q",
        "plan": ["p1", "p2"],
        "steps": ["o1", "o2"],
        "verify_results": [{"status": "pass", "reasons": []}, {"status": "pass", "reasons": []}],
        "quality": {"confidence": 0.8},
        "timeline": {},
        "answer": "A",
    }
    replay_a = replay_reasoning_trace(trace=trace)
    replay_b = replay_reasoning_trace(trace=trace)
    assert replay_a == replay_b


def test_replay_reasoning_trace_payload_reproduces_same_result():
    trace = {
        "query": "Q",
        "plan": ["step"],
        "steps": ["output"],
        "verify_results": [{"status": "pass", "reasons": []}],
        "quality": {},
        "timeline": {},
        "answer": "A",
    }
    payload = serialize_reasoning_trace(trace=trace)
    assert replay_reasoning_trace_payload(payload=payload) == replay_reasoning_trace(trace=trace)
