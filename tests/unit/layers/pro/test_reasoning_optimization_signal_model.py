from __future__ import annotations

from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    build_reasoning_optimization_signal,
    build_reasoning_optimization_signal_from_diagnostics,
)


def test_build_reasoning_optimization_signal_normalizes_values():
    signal = build_reasoning_optimization_signal(
        trace_id=" trace-1 ",
        confidence_score="1.2",
        coverage_score="-1",
        pass_rate="0.75",
        average_latency_ms="-10",
        warnings_count="3",
        retry_rate="yes",
        signal_tags=["low_confidence", " low_confidence ", "", "retry_pressure"],
    )
    assert signal == {
        "trace_id": "trace-1",
        "confidence_score": 1.0,
        "coverage_score": 0.0,
        "pass_rate": 0.75,
        "average_latency_ms": 0,
        "warnings_count": 3,
        "retry_rate": 0.0,
        "signal_tags": ["low_confidence", "retry_pressure"],
    }


def test_build_reasoning_optimization_signal_from_diagnostics_extracts_metrics():
    signal = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics={
            "trace_id": "t-1",
            "reasoning_quality": {
                "confidence": {"confidence_score": 0.4},
                "coverage": {"coverage_score": 0.5},
                "retry": {"should_retry": True},
            },
            "reasoning_benchmark": {
                "average_latency_ms": 42,
                "summary": {"pass_rate": 0.25},
            },
        },
        warnings=["verify_warning"],
    )
    assert signal == {
        "trace_id": "t-1",
        "confidence_score": 0.4,
        "coverage_score": 0.5,
        "pass_rate": 0.25,
        "average_latency_ms": 42,
        "warnings_count": 1,
        "retry_rate": 1.0,
        "signal_tags": [
            "low_confidence",
            "low_coverage",
            "retry_pressure",
            "warnings_present",
        ],
    }


def test_build_reasoning_optimization_signal_from_diagnostics_defaults_when_missing():
    signal = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics={},
        warnings=[],
    )
    assert signal == {
        "trace_id": "",
        "confidence_score": 0.0,
        "coverage_score": 0.0,
        "pass_rate": 0.0,
        "average_latency_ms": 0,
        "warnings_count": 0,
        "retry_rate": 0.0,
        "signal_tags": ["low_confidence", "low_coverage"],
    }
