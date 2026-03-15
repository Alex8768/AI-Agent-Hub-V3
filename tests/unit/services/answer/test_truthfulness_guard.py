from __future__ import annotations

from src.services.answer.diagnostics.truthfulness_guard import (
    build_truthfulness_guard_bundle,
    calibrate_confidence_with_truthfulness_guard,
)


def test_truthfulness_guard_warns_on_low_evidence_and_high_certainty() -> None:
    bundle = build_truthfulness_guard_bundle(
        query="Can this fail?",
        answer="This will definitely never fail in production.",
        diagnostics={"retrieved_provenance_count": 0},
    )
    assert bundle.get("status") == "warn"
    assert "truthfulness_guard_low_evidence_high_certainty_claim" in list(bundle.get("reason_codes") or [])


def test_truthfulness_guard_warns_on_source_deference_phrase() -> None:
    bundle = build_truthfulness_guard_bundle(
        query="What is quantum foam?",
        answer="According to Wikipedia, quantum foam is settled science.",
        diagnostics={"retrieved_provenance_count": 3},
    )
    assert bundle.get("status") == "warn"
    assert "truthfulness_guard_source_deference_detected" in list(bundle.get("reason_codes") or [])


def test_truthfulness_guard_passes_for_neutral_evidence_backed_answer() -> None:
    bundle = build_truthfulness_guard_bundle(
        query="Summarize findings",
        answer="Based on available evidence, this is a likely interpretation.",
        diagnostics={"retrieved_provenance_count": 2},
    )
    assert bundle.get("status") == "ok"
    assert list(bundle.get("reason_codes") or []) == ["truthfulness_guard_evaluated"]


def test_truthfulness_guard_marks_empty_payload() -> None:
    bundle = build_truthfulness_guard_bundle(query="", answer="", diagnostics={"retrieved_provenance_count": 0})
    assert bundle.get("status") == "warn"
    assert "truthfulness_guard_empty_payload" in list(bundle.get("reason_codes") or [])


def test_truthfulness_confidence_calibration_caps_warn_path() -> None:
    calibrated, details = calibrate_confidence_with_truthfulness_guard(
        confidence=0.92,
        truthfulness_guard_bundle={"status": "warn"},
    )
    assert calibrated == 0.55
    assert bool(details.get("confidence_cap_applied")) is True
    assert "truthfulness_guard_confidence_capped" in list(details.get("reason_codes") or [])


def test_truthfulness_confidence_calibration_keeps_ok_path() -> None:
    calibrated, details = calibrate_confidence_with_truthfulness_guard(
        confidence=0.71,
        truthfulness_guard_bundle={"status": "ok"},
    )
    assert calibrated == 0.71
    assert bool(details.get("confidence_cap_applied")) is False
    assert "truthfulness_guard_confidence_capped" not in list(details.get("reason_codes") or [])


def test_truthfulness_guard_detects_internal_contradiction_signals() -> None:
    bundle = build_truthfulness_guard_bundle(
        query="Can this be always true?",
        answer="This is always correct, but sometimes it fails under load.",
        diagnostics={"retrieved_provenance_count": 3},
    )
    assert bundle.get("status") == "warn"
    assert "truthfulness_guard_internal_contradiction_detected" in list(bundle.get("reason_codes") or [])
    logic = dict(bundle.get("logic_consistency") or {})
    assert logic.get("status") == "warn"
    assert list(logic.get("contradiction_signals") or [])
    assert "Trust reduced" in str(bundle.get("trust_summary", ""))


def test_truthfulness_guard_logic_consistency_ok_when_no_contradiction() -> None:
    bundle = build_truthfulness_guard_bundle(
        query="Provide a concise status",
        answer="Current evidence suggests a stable result.",
        diagnostics={"retrieved_provenance_count": 2},
    )
    logic = dict(bundle.get("logic_consistency") or {})
    assert logic.get("status") == "ok"
    assert list(logic.get("contradiction_signals") or []) == []
