from __future__ import annotations

from src.layers.pro.anticipatory.scanner import (
    OpportunityScanner,
    build_opportunity_scan_result,
    build_opportunity_signal,
)


def test_build_opportunity_signal_normalizes_fields() -> None:
    signal = build_opportunity_signal(
        signal_id=" s1 ",
        category="SUMMARIZATION",
        confidence=1.2,
        trigger=" doc ",
        rationale=" test ",
    )
    assert signal == {
        "signal_id": "s1",
        "category": "summarization",
        "confidence": 1.0,
        "trigger": "doc",
        "rationale": "test",
    }


def test_build_opportunity_scan_result_is_deterministic() -> None:
    signals = [
        {"signal_id": "b", "category": "follow_up", "confidence": 0.7, "trigger": "t2", "rationale": "r2"},
        {"signal_id": "a", "category": "automation", "confidence": 0.8, "trigger": "t1", "rationale": "r1"},
    ]
    result_a = build_opportunity_scan_result(signals=signals, min_confidence=0.6)
    result_b = build_opportunity_scan_result(signals=list(reversed(signals)), min_confidence=0.6)
    assert result_a == result_b
    assert result_a["status"] == "active"
    assert result_a["reason_codes"] == ["opportunities_detected"]


def test_opportunity_scanner_scan_detects_expected_signals() -> None:
    scanner = OpportunityScanner()
    result = scanner.scan(
        context="Analyze this document and propose next plan",
        session_memory="unresolved action pending",
        registry={"enabled": True},
        min_confidence=0.6,
    )
    signal_ids = [x["signal_id"] for x in result["signals"]]
    assert result["status"] == "active"
    assert "scan_summarization" in signal_ids
    assert "scan_follow_up" in signal_ids
    assert "scan_memory_pending" in signal_ids
    assert "scan_registry_available" in signal_ids
