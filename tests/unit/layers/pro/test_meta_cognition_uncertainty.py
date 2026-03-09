from __future__ import annotations

from src.layers.pro.meta_cognition.uncertainty import (
    UncertaintyTracker,
    build_uncertainty_signal,
    build_uncertainty_summary,
)


def test_build_uncertainty_signal_normalizes_fields() -> None:
    signal = build_uncertainty_signal(
        code=" LOW_EVIDENCE  ",
        severity="HIGH",
        confidence=1.2,
        source=" verify ",
        message="  sparse evidence  ",
    )
    assert signal == {
        "code": "low_evidence",
        "severity": "high",
        "confidence": 1.0,
        "source": "verify",
        "message": "sparse evidence",
    }


def test_build_uncertainty_summary_is_deterministic() -> None:
    signals = [
        {"code": "low_conf", "severity": "high", "confidence": 0.2, "source": "planner"},
        {"code": "contradiction", "severity": "critical", "confidence": 0.1, "source": "verify"},
    ]
    summary_a = build_uncertainty_summary(signals=signals)
    summary_b = build_uncertainty_summary(signals=list(reversed(signals)))
    assert summary_a == summary_b
    assert summary_a["status"] in {"medium", "high"}
    assert "high_severity_signal" in summary_a["reason_codes"]


def test_uncertainty_tracker_collects_and_clears() -> None:
    tracker = UncertaintyTracker()
    tracker.record(
        signal={"code": "missing_data", "severity": "medium", "confidence": 0.3, "source": "retrieval"}
    )
    tracker.record(
        signal={"code": "contradiction", "severity": "critical", "confidence": 0.1, "source": "verify"}
    )
    snapshot = tracker.snapshot()
    assert len(snapshot) == 2
    summary = tracker.build_summary()
    assert summary["uncertainty_score"] > 0.0
    assert summary["status"] in {"medium", "high"}
    tracker.clear()
    assert tracker.snapshot() == []
