from __future__ import annotations

import pytest

from src.layers.pro.reasoning.trace.trace_serializer import (
    deserialize_reasoning_trace,
    serialize_reasoning_trace,
)


def test_serialize_reasoning_trace_is_deterministic():
    trace = {
        "query": "Q",
        "plan": ["step one", "step two"],
        "steps": ["out one", "out two"],
        "verify_results": [
            {"status": "pass", "reasons": []},
            {"status": "warn", "reasons": ["needs_support"]},
        ],
        "quality": {"confidence": 0.9, "coverage": 1.0},
        "answer": "A",
    }
    payload_a = serialize_reasoning_trace(trace=trace)
    payload_b = serialize_reasoning_trace(trace=trace)
    assert payload_a == payload_b
    assert payload_a == (
        '{"answer":"A","plan":["step one","step two"],'
        '"quality":{"confidence":0.9,"coverage":1.0},"query":"Q",'
        '"steps":["out one","out two"],'
        '"verify_results":[{"reasons":[],"status":"pass"},'
        '{"reasons":["needs_support"],"status":"warn"}]}'
    )


def test_deserialize_reasoning_trace_normalizes_shape():
    payload = (
        '{"query":"  Q  ","plan":["  s1  "," "],"steps":["  out  "],'
        '"verify_results":[{"status":" pass ","reasons":["  r1  "," "]}],'
        '"quality":{"x":1},"answer":"  A  "}'
    )
    trace = deserialize_reasoning_trace(payload=payload)
    assert trace == {
        "query": "Q",
        "plan": ["s1"],
        "steps": ["out"],
        "verify_results": [{"status": "pass", "reasons": ["r1"]}],
        "quality": {"x": 1},
        "answer": "A",
    }


def test_deserialize_reasoning_trace_rejects_non_object_json():
    with pytest.raises(ValueError, match="JSON object"):
        deserialize_reasoning_trace(payload='["not-an-object"]')
