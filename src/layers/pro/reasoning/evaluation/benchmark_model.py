from __future__ import annotations

from typing import TypedDict


class ReasoningBenchmarkCase(TypedDict):
    case_id: str
    query: str
    expected_signals: list[str]
    tags: list[str]
    weight: float


class ReasoningBenchmarkResult(TypedDict):
    case_id: str
    score: float
    passed: bool
    reasons: list[str]
    latency_ms: int


class ReasoningBenchmarkRunSummary(TypedDict):
    suite_name: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_score: float
    results: list[ReasoningBenchmarkResult]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_int(value: object, *, default: int = 0, min_value: int = 0, max_value: int = 3_600_000) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_reasoning_benchmark_case(
    *,
    case_id: object,
    query: object,
    expected_signals: object = None,
    tags: object = None,
    weight: object = 1.0,
) -> ReasoningBenchmarkCase:
    """Build normalized reasoning benchmark case contract."""
    return {
        "case_id": _normalize_string(case_id),
        "query": _normalize_string(query),
        "expected_signals": _normalize_string_list(expected_signals),
        "tags": _normalize_string_list(tags),
        "weight": _normalize_float_01(weight, default=1.0),
    }


def build_reasoning_benchmark_result(
    *,
    case_id: object,
    score: object,
    passed: object,
    reasons: object = None,
    latency_ms: object = 0,
) -> ReasoningBenchmarkResult:
    """Build normalized benchmark result contract."""
    normalized_score = _normalize_float_01(score, default=0.0)
    normalized_passed = bool(passed)
    return {
        "case_id": _normalize_string(case_id),
        "score": normalized_score,
        "passed": normalized_passed,
        "reasons": _normalize_string_list(reasons),
        "latency_ms": _normalize_int(latency_ms, default=0, min_value=0),
    }


def build_reasoning_benchmark_run_summary(
    *,
    suite_name: object,
    results: list[dict[str, object]],
) -> ReasoningBenchmarkRunSummary:
    """Build deterministic benchmark run summary from case-level results."""
    normalized_results: list[ReasoningBenchmarkResult] = []
    for raw in list(results or []):
        row = raw if isinstance(raw, dict) else {}
        case_id = _normalize_string(row.get("case_id", ""))
        if not case_id:
            continue
        normalized_results.append(
            build_reasoning_benchmark_result(
                case_id=case_id,
                score=row.get("score", 0.0),
                passed=row.get("passed", False),
                reasons=row.get("reasons", []),
                latency_ms=row.get("latency_ms", 0),
            )
        )

    normalized_results.sort(key=lambda x: str(x["case_id"]))
    total_cases = int(len(normalized_results))
    passed_cases = int(sum(1 for x in normalized_results if bool(x["passed"])))
    average_score = (
        float(sum(float(x["score"]) for x in normalized_results) / float(total_cases))
        if total_cases > 0
        else 0.0
    )
    pass_rate = (float(passed_cases) / float(total_cases)) if total_cases > 0 else 0.0
    return {
        "suite_name": _normalize_string(suite_name),
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": _normalize_float_01(pass_rate, default=0.0),
        "average_score": _normalize_float_01(average_score, default=0.0),
        "results": normalized_results,
    }
