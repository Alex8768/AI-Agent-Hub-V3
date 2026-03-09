from __future__ import annotations

from typing import Callable, TypedDict

from src.layers.pro.reasoning.evaluation.benchmark_model import (
    ReasoningBenchmarkCase,
    ReasoningBenchmarkResult,
    ReasoningBenchmarkRunSummary,
    build_reasoning_benchmark_result,
    build_reasoning_benchmark_run_summary,
)
from src.layers.pro.reasoning.evaluation.benchmark_registry import ReasoningBenchmarkSuite


class ReasoningBenchmarkRunOutcome(TypedDict):
    suite_name: str
    summary: ReasoningBenchmarkRunSummary
    failed_case_ids: list[str]
    average_latency_ms: int
    results: list[ReasoningBenchmarkResult]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_int(value: object, *, default: int = 0, min_value: int = 0, max_value: int = 3_600_000) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def run_reasoning_benchmark_suite(
    *,
    suite: ReasoningBenchmarkSuite,
    evaluate_case: Callable[[ReasoningBenchmarkCase], dict[str, object]],
) -> ReasoningBenchmarkRunOutcome:
    """Run a benchmark suite using a deterministic case-order contract."""
    suite_name = _normalize_string(suite.get("suite_name", ""))
    results: list[ReasoningBenchmarkResult] = []

    for case in list(suite.get("cases") or []):
        try:
            evaluation = dict(evaluate_case(case) or {})
            score = evaluation.get("score", 0.0)
            passed = evaluation.get("passed", False)
            reasons = evaluation.get("reasons", [])
            latency_ms = evaluation.get("latency_ms", 0)
        except Exception as exc:  # deterministic failure contract for runner callers
            score = 0.0
            passed = False
            reasons = [f"evaluator_error:{type(exc).__name__}"]
            latency_ms = 0

        results.append(
            build_reasoning_benchmark_result(
                case_id=case.get("case_id", ""),
                score=score,
                passed=passed,
                reasons=reasons,
                latency_ms=latency_ms,
            )
        )

    summary = build_reasoning_benchmark_run_summary(
        suite_name=suite_name,
        results=[dict(x) for x in list(results or [])],
    )
    failed_case_ids = [
        str(row.get("case_id", "") or "")
        for row in list(summary.get("results") or [])
        if not bool(row.get("passed", False))
    ]
    latencies = [int(row.get("latency_ms", 0) or 0) for row in list(summary.get("results") or [])]
    average_latency_ms = (
        int(sum(latencies) / len(latencies))
        if len(latencies) > 0
        else 0
    )
    return {
        "suite_name": suite_name,
        "summary": summary,
        "failed_case_ids": failed_case_ids,
        "average_latency_ms": _normalize_int(average_latency_ms, default=0, min_value=0),
        "results": list(summary.get("results") or []),
    }
