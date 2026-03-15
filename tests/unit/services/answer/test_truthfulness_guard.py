from __future__ import annotations

from src.services.answer.diagnostics.truthfulness_guard import build_truthfulness_guard_bundle


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
