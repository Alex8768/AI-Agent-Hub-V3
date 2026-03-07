from __future__ import annotations

from src.layers.pro.reasoning.trace.trace_model import build_reasoning_trace


def test_build_reasoning_trace_keeps_expected_contract_shape():
    trace = build_reasoning_trace(
        query="What is the capital of France?",
        plan=["find capital", "verify country relation"],
        steps=["capital=Paris", "relation=France->Paris"],
        verify_results=[
            {"status": "pass", "reasons": []},
            {"status": "pass", "reasons": ["supported by evidence"]},
        ],
        quality={"coverage": 1.0, "confidence": 0.95},
        answer="Paris is the capital of France.",
    )
    assert trace == {
        "query": "What is the capital of France?",
        "plan": ["find capital", "verify country relation"],
        "steps": ["capital=Paris", "relation=France->Paris"],
        "verify_results": [
            {"status": "pass", "reasons": []},
            {"status": "pass", "reasons": ["supported by evidence"]},
        ],
        "quality": {"coverage": 1.0, "confidence": 0.95},
        "answer": "Paris is the capital of France.",
    }


def test_build_reasoning_trace_normalizes_whitespace_and_empty_values():
    trace = build_reasoning_trace(
        query="  query  ",
        plan=["  step one  ", "", "   ", "step two"],
        steps=["  output one  ", " ", "output two"],
        verify_results=[
            {"status": " warn ", "reasons": ["  r1  ", "", "   "]},
            {"status": None, "reasons": "  only-reason  "},
        ],
        quality={"score": 0.7},
        answer="  final  ",
    )
    assert trace["query"] == "query"
    assert trace["plan"] == ["step one", "step two"]
    assert trace["steps"] == ["output one", "output two"]
    assert trace["verify_results"] == [
        {"status": "warn", "reasons": ["r1"]},
        {"status": "", "reasons": ["only-reason"]},
    ]
    assert trace["quality"] == {"score": 0.7}
    assert trace["answer"] == "final"


def test_build_reasoning_trace_handles_empty_inputs_with_stable_defaults():
    trace = build_reasoning_trace(
        query="",
        plan=[],
        steps=[],
        verify_results=[],
        quality={},
        answer="",
    )
    assert trace == {
        "query": "",
        "plan": [],
        "steps": [],
        "verify_results": [],
        "quality": {},
        "answer": "",
    }
