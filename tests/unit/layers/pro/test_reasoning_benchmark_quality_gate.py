from __future__ import annotations

from src.layers.pro.reasoning.evaluation.benchmark_model import (
    build_reasoning_benchmark_case,
    build_reasoning_benchmark_run_summary,
)
from src.layers.pro.reasoning.evaluation.benchmark_registry import (
    build_reasoning_benchmark_registry,
    build_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.evaluation.benchmark_runner import (
    run_reasoning_benchmark_suite,
)


def _suite():
    return build_reasoning_benchmark_suite(
        suite_name="reasoning-smoke",
        owner="qa",
        tags=["smoke", "reasoning"],
        cases=[
            {"case_id": "b", "query": "q2", "expected_signals": ["verify_pass"]},
            {"case_id": "a", "query": "q1", "expected_signals": ["verify_pass"]},
        ],
    )


def test_benchmark_quality_gate_case_and_registry_are_deterministic():
    case_a = build_reasoning_benchmark_case(
        case_id=" c-1 ",
        query=" q ",
        expected_signals=["signal", " signal "],
        tags=["t1", "t1"],
        weight="0.8",
    )
    case_b = build_reasoning_benchmark_case(
        case_id=" c-1 ",
        query=" q ",
        expected_signals=["signal", " signal "],
        tags=["t1", "t1"],
        weight="0.8",
    )
    assert case_a == case_b

    reg_a = build_reasoning_benchmark_registry(
        suites=[
            {"suite_name": "z", "cases": [{"case_id": "c1", "query": "q"}]},
            {"suite_name": "a", "cases": [{"case_id": "c2", "query": "q"}]},
        ]
    )
    reg_b = build_reasoning_benchmark_registry(
        suites=[
            {"suite_name": "z", "cases": [{"case_id": "c1", "query": "q"}]},
            {"suite_name": "a", "cases": [{"case_id": "c2", "query": "q"}]},
        ]
    )
    assert reg_a == reg_b


def test_benchmark_quality_gate_runner_is_deterministic():
    suite = _suite()

    def _evaluate(case):
        cid = str(case.get("case_id", "") or "")
        if cid == "a":
            return {"score": 1.0, "passed": True, "latency_ms": 10}
        return {"score": 0.2, "passed": False, "latency_ms": 30, "reasons": ["low_score"]}

    run_a = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    run_b = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    assert run_a == run_b


def test_benchmark_quality_gate_summary_parity():
    summary = build_reasoning_benchmark_run_summary(
        suite_name="reasoning-smoke",
        results=[
            {"case_id": "a", "score": 1.0, "passed": True, "latency_ms": 10},
            {"case_id": "b", "score": 0.0, "passed": False, "latency_ms": 20},
        ],
    )
    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 1
    assert summary["pass_rate"] == 0.5
    assert summary["average_score"] == 0.5


def test_benchmark_quality_gate_runner_contract_shape():
    suite = _suite()

    def _evaluate(case):
        _ = case
        return {"score": 0.5, "passed": True, "latency_ms": 5}

    run = run_reasoning_benchmark_suite(suite=suite, evaluate_case=_evaluate)
    assert set(run.keys()) == {
        "suite_name",
        "summary",
        "failed_case_ids",
        "average_latency_ms",
        "results",
    }
    assert set(dict(run["summary"]).keys()) == {
        "suite_name",
        "total_cases",
        "passed_cases",
        "pass_rate",
        "average_score",
        "results",
    }
