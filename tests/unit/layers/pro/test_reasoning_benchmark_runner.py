from __future__ import annotations

from src.layers.pro.reasoning.evaluation.benchmark_registry import (
    build_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.evaluation.benchmark_runner import (
    run_reasoning_benchmark_suite,
)


def _sample_suite():
    return build_reasoning_benchmark_suite(
        suite_name="smoke",
        owner="qa",
        tags=["reasoning"],
        cases=[
            {"case_id": "b", "query": "q2"},
            {"case_id": "a", "query": "q1"},
        ],
    )


def test_run_reasoning_benchmark_suite_is_deterministic():
    suite = _sample_suite()

    def _evaluate(case):
        cid = str(case.get("case_id", "") or "")
        if cid == "a":
            return {"score": 0.9, "passed": True, "reasons": [], "latency_ms": 10}
        return {"score": 0.4, "passed": False, "reasons": ["low_score"], "latency_ms": 30}

    run_a = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    run_b = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    assert run_a == run_b


def test_run_reasoning_benchmark_suite_builds_summary_and_failed_case_ids():
    suite = _sample_suite()

    def _evaluate(case):
        cid = str(case.get("case_id", "") or "")
        return {"score": 1.0 if cid == "a" else 0.0, "passed": cid == "a", "latency_ms": 25}

    run = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    summary = dict(run.get("summary") or {})

    assert run["suite_name"] == "smoke"
    assert summary.get("total_cases") == 2
    assert summary.get("passed_cases") == 1
    assert summary.get("pass_rate") == 0.5
    assert summary.get("average_score") == 0.5
    assert run["failed_case_ids"] == ["b"]
    assert run["average_latency_ms"] == 25


def test_run_reasoning_benchmark_suite_handles_evaluator_errors():
    suite = _sample_suite()

    def _evaluate(case):
        cid = str(case.get("case_id", "") or "")
        if cid == "b":
            raise RuntimeError("boom")
        return {"score": 1.0, "passed": True, "latency_ms": 5}

    run = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    results = list(run.get("results") or [])
    row_b = next(x for x in results if x["case_id"] == "b")
    assert row_b["passed"] is False
    assert row_b["score"] == 0.0
    assert any(str(x).startswith("evaluator_error:") for x in row_b["reasons"])
