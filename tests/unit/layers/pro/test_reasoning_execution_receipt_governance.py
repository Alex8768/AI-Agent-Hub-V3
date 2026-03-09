from __future__ import annotations

from src.layers.pro.reasoning.governance.receipt_collector import (
    collect_reasoning_execution_receipt,
)
from src.layers.pro.reasoning.governance.receipt_serializer import (
    deserialize_reasoning_execution_receipt,
    serialize_reasoning_execution_receipt,
)
from src.layers.pro.reasoning.governance.replay import (
    replay_reasoning_execution_receipt,
    replay_reasoning_execution_receipt_payload,
)


def _sample_diagnostics() -> dict[str, object]:
    return {
        "reasoning_quality": {"confidence": {"confidence_score": 0.85}},
        "top_evidence": ["chunk:c1", "memory:session:s1:last_answer"],
        "self_check": {"status": "pass", "reasons": []},
        "verify": {"status": "warn", "reasons": ["coverage_low"]},
        "reasoning_execution_policy": {
            "max_steps": 3,
            "max_retries": 1,
            "max_latency_ms": 15000,
        },
        "evidence_contract_valid_minimal": False,
    }


def test_governance_receipt_deterministic_across_identical_runs():
    receipt_a = collect_reasoning_execution_receipt(
        trace_id="trace-1",
        replay_token="",
        query="Q",
        answer="A",
        diagnostics=_sample_diagnostics(),
        warnings=["verify_warning"],
    )
    receipt_b = collect_reasoning_execution_receipt(
        trace_id="trace-1",
        replay_token="",
        query="Q",
        answer="A",
        diagnostics=_sample_diagnostics(),
        warnings=["verify_warning"],
    )
    assert receipt_a == receipt_b


def test_governance_receipt_roundtrip_preserves_contract_shape():
    receipt = collect_reasoning_execution_receipt(
        trace_id="trace-2",
        replay_token="",
        query="Q2",
        answer="A2",
        diagnostics=_sample_diagnostics(),
        warnings=["verify_warning"],
    )
    payload = serialize_reasoning_execution_receipt(receipt=receipt)
    restored = deserialize_reasoning_execution_receipt(payload=payload)
    assert restored == replay_reasoning_execution_receipt(receipt=receipt)
    assert restored["replay_token"] == "replay:trace-2"
    assert set(restored.keys()) == {
        "version",
        "trace_id",
        "replay_token",
        "query",
        "answer",
        "confidence_score",
        "sources",
        "policy_decisions",
        "risk_flags",
    }


def test_governance_receipt_replay_payload_matches_object_replay():
    receipt = collect_reasoning_execution_receipt(
        trace_id="trace-3",
        replay_token="",
        query="Q3",
        answer="A3",
        diagnostics=_sample_diagnostics(),
        warnings=["verify_warning"],
    )
    payload = serialize_reasoning_execution_receipt(receipt=receipt)
    assert replay_reasoning_execution_receipt_payload(payload=payload) == replay_reasoning_execution_receipt(
        receipt=receipt
    )


def test_governance_receipt_contains_expected_policy_and_risk_markers():
    receipt = collect_reasoning_execution_receipt(
        trace_id="trace-4",
        replay_token="",
        query="Q4",
        answer="A4",
        diagnostics=_sample_diagnostics(),
        warnings=["verify_warning"],
    )
    decision_names = [row["policy_name"] for row in receipt["policy_decisions"]]
    assert "self_check" in decision_names
    assert "verify" in decision_names
    assert "execution_policy" in decision_names
    assert "verify_warning" in receipt["risk_flags"]
    assert "verify_warn" in receipt["risk_flags"]
    assert "evidence_contract_minimal_invalid" in receipt["risk_flags"]
