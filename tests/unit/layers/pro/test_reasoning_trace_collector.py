from __future__ import annotations

from src.layers.pro.reasoning.trace.trace_collector import collect_reasoning_trace


def test_collect_reasoning_trace_builds_expected_contract():
    trace = collect_reasoning_trace(
        query="Find capital and verify relation",
        plan={"steps": [{"description": "find capital"}, {"description": "verify relation"}]},
        step_results=[
            {
                "step_index": 0,
                "step_description": "find capital",
                "reasoning_output": "capital=Paris",
                "verify_status": "pass",
                "verify_reasons": [],
            },
            {
                "step_index": 1,
                "step_description": "verify relation",
                "reasoning_output": "Paris is in France",
                "verify_status": "pass",
                "verify_reasons": ["supported"],
            },
        ],
        quality={"coverage": 1.0, "confidence": 0.9},
        answer="Paris is the capital of France.",
    )
    assert trace == {
        "query": "Find capital and verify relation",
        "plan": ["find capital", "verify relation"],
        "steps": ["capital=Paris", "Paris is in France"],
        "verify_results": [
            {"status": "pass", "reasons": []},
            {"status": "pass", "reasons": ["supported"]},
        ],
        "quality": {"coverage": 1.0, "confidence": 0.9},
        "answer": "Paris is the capital of France.",
    }


def test_collect_reasoning_trace_normalizes_missing_fields():
    trace = collect_reasoning_trace(
        query="  query  ",
        plan={"steps": [{"description": "  step one  "}, {}, {"description": "   "}]},
        step_results=[
            {"reasoning_output": "  out one  ", "verify_status": " warn ", "verify_reasons": ["  r1  ", " "]},
            {"reasoning_output": "", "verify_status": "", "verify_reasons": []},
        ],
        quality={},
        answer="  answer  ",
    )
    assert trace["query"] == "query"
    assert trace["plan"] == ["step one"]
    assert trace["steps"] == ["out one"]
    assert trace["verify_results"] == [
        {"status": "warn", "reasons": ["r1"]},
        {"status": "", "reasons": []},
    ]
    assert trace["quality"] == {}
    assert trace["answer"] == "answer"


def test_collect_reasoning_trace_handles_empty_structures():
    trace = collect_reasoning_trace(
        query="",
        plan={},
        step_results=[],
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
