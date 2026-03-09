from __future__ import annotations

from src.layers.pro.reasoning.evaluation.benchmark_model import (
    build_reasoning_benchmark_case,
    build_reasoning_benchmark_result,
    build_reasoning_benchmark_run_summary,
)


def test_build_reasoning_benchmark_case_normalizes_values():
    case = build_reasoning_benchmark_case(
        case_id="  c-1 ",
        query="  What is graph reasoning? ",
        expected_signals=["source_refs", " source_refs ", "", "confidence"],
        tags=["core", " core ", "reasoning"],
        weight="2.4",
    )
    assert case == {
        "case_id": "c-1",
        "query": "What is graph reasoning?",
        "expected_signals": ["confidence", "source_refs"],
        "tags": ["core", "reasoning"],
        "weight": 1.0,
    }


def test_build_reasoning_benchmark_result_normalizes_values():
    result = build_reasoning_benchmark_result(
        case_id=" c-2 ",
        score="0.77",
        passed=1,
        reasons=["", "good coverage", " good coverage "],
        latency_ms="-10",
    )
    assert result == {
        "case_id": "c-2",
        "score": 0.77,
        "passed": True,
        "reasons": ["good coverage"],
        "latency_ms": 0,
    }


def test_build_reasoning_benchmark_run_summary_is_deterministic():
    summary = build_reasoning_benchmark_run_summary(
        suite_name="  smoke ",
        results=[
            {
                "case_id": "b",
                "score": 0.2,
                "passed": False,
                "reasons": ["low_score"],
                "latency_ms": 100,
            },
            {
                "case_id": "a",
                "score": 0.8,
                "passed": True,
                "reasons": [],
                "latency_ms": 50,
            },
            {
                "case_id": " ",
                "score": 1.0,
                "passed": True,
                "reasons": [],
                "latency_ms": 1,
            },
        ],
    )
    assert summary["suite_name"] == "smoke"
    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 1
    assert summary["pass_rate"] == 0.5
    assert summary["average_score"] == 0.5
    assert [row["case_id"] for row in summary["results"]] == ["a", "b"]
