from __future__ import annotations

from src.layers.pro.meta_cognition.reflection import build_reflection_insight, build_reflection_report


def test_build_reflection_insight_normalizes_values() -> None:
    insight = build_reflection_insight(code=" LOW_SUPPORT ", message="  add evidence ", severity="HIGH")
    assert insight == {
        "code": "low_support",
        "message": "add evidence",
        "severity": "high",
    }


def test_build_reflection_report_is_deterministic_and_merges_reason_codes() -> None:
    uncertainty = {
        "uncertainty_score": 0.6,
        "reason_codes": ["high_severity_signal"],
        "warnings": ["unclear_source"],
    }
    gap_map = {
        "coverage_score": 0.5,
        "reason_codes": ["gaps_present"],
        "warnings": ["missing_dataset"],
    }
    insights = [
        {"code": "B", "message": "second", "severity": "low"},
        {"code": "A", "message": "first", "severity": "critical"},
    ]
    report_a = build_reflection_report(
        uncertainty_summary=uncertainty,
        gap_map=gap_map,
        insights=insights,
        warnings=["manual_warning"],
    )
    report_b = build_reflection_report(
        uncertainty_summary=uncertainty,
        gap_map=gap_map,
        insights=list(reversed(insights)),
        warnings=["manual_warning"],
    )
    assert report_a == report_b
    assert report_a["status"] == "rework"
    assert "low_reflection_confidence" in report_a["reason_codes"]
    assert report_a["warnings"] == ["manual_warning", "missing_dataset", "unclear_source"]


def test_build_reflection_report_ready_path() -> None:
    report = build_reflection_report(
        uncertainty_summary={"uncertainty_score": 0.1},
        gap_map={"coverage_score": 0.95},
        insights=[],
    )
    assert report["status"] == "ready"
    assert report["confidence_score"] > 0.7
