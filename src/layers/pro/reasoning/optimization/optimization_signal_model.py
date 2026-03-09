from __future__ import annotations

from typing import TypedDict


class ReasoningOptimizationSignal(TypedDict):
    trace_id: str
    confidence_score: float
    coverage_score: float
    pass_rate: float
    average_latency_ms: int
    warnings_count: int
    retry_rate: float
    signal_tags: list[str]


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


def build_reasoning_optimization_signal(
    *,
    trace_id: object,
    confidence_score: object,
    coverage_score: object,
    pass_rate: object,
    average_latency_ms: object,
    warnings_count: object,
    retry_rate: object,
    signal_tags: object = None,
) -> ReasoningOptimizationSignal:
    """Build normalized optimization signal contract from runtime metrics."""
    return {
        "trace_id": _normalize_string(trace_id),
        "confidence_score": _normalize_float_01(confidence_score, default=0.0),
        "coverage_score": _normalize_float_01(coverage_score, default=0.0),
        "pass_rate": _normalize_float_01(pass_rate, default=0.0),
        "average_latency_ms": _normalize_int(average_latency_ms, default=0, min_value=0),
        "warnings_count": _normalize_int(warnings_count, default=0, min_value=0, max_value=1_000_000),
        "retry_rate": _normalize_float_01(retry_rate, default=0.0),
        "signal_tags": _normalize_string_list(signal_tags),
    }


def build_reasoning_optimization_signal_from_diagnostics(
    *,
    diagnostics: dict[str, object] | None,
    warnings: list[str] | None = None,
) -> ReasoningOptimizationSignal:
    """Build optimization signal from reasoning diagnostics snapshot."""
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    quality = dict(diag.get("reasoning_quality") or {})
    confidence = dict(quality.get("confidence") or {})
    coverage = dict(quality.get("coverage") or {})
    retry = dict(quality.get("retry") or {})
    benchmark = dict(diag.get("reasoning_benchmark") or {})
    benchmark_summary = dict(benchmark.get("summary") or {})

    tags: list[str] = []
    if bool(retry.get("should_retry", False)):
        tags.append("retry_pressure")
    if float(confidence.get("confidence_score", 0.0) or 0.0) < 0.6:
        tags.append("low_confidence")
    if float(coverage.get("coverage_score", 0.0) or 0.0) < 0.6:
        tags.append("low_coverage")
    if int(len(list(warnings or []))) > 0:
        tags.append("warnings_present")

    return build_reasoning_optimization_signal(
        trace_id=diag.get("trace_id", ""),
        confidence_score=confidence.get("confidence_score", 0.0),
        coverage_score=coverage.get("coverage_score", 0.0),
        pass_rate=benchmark_summary.get("pass_rate", 0.0),
        average_latency_ms=benchmark.get("average_latency_ms", 0),
        warnings_count=int(len(list(warnings or []))),
        retry_rate=1.0 if bool(retry.get("should_retry", False)) else 0.0,
        signal_tags=tags,
    )
