from __future__ import annotations

from src.layers.pro.reasoning.governance.replay import (
    replay_reasoning_execution_receipt,
    replay_reasoning_execution_receipt_payload,
)
from src.layers.pro.reasoning.governance.receipt_serializer import (
    serialize_reasoning_execution_receipt,
)


def test_replay_reasoning_execution_receipt_roundtrip_reproduces_normalized_receipt():
    receipt = {
        "trace_id": "  trace-1  ",
        "replay_token": "",
        "query": "  Q  ",
        "answer": "  A  ",
        "confidence_score": 0.8,
        "sources": [{"source_id": " c1 ", "source_type": " chunk ", "confidence": 0.7}],
        "policy_decisions": [{"policy_name": " verify ", "status": " pass ", "reason": " "}],
        "risk_flags": [" warn ", ""],
    }
    replayed = replay_reasoning_execution_receipt(receipt=receipt)
    assert replayed == {
        "version": "v1",
        "trace_id": "trace-1",
        "replay_token": "replay:trace-1",
        "query": "Q",
        "answer": "A",
        "confidence_score": 0.8,
        "sources": [{"source_id": "c1", "source_type": "chunk", "confidence": 0.7}],
        "policy_decisions": [{"policy_name": "verify", "status": "pass", "reason": ""}],
        "risk_flags": ["warn"],
    }


def test_replay_reasoning_execution_receipt_is_deterministic_across_runs():
    receipt = {
        "trace_id": "trace-2",
        "replay_token": "replay:trace-2",
        "query": "Q",
        "answer": "A",
        "confidence_score": 0.4,
        "sources": [],
        "policy_decisions": [],
        "risk_flags": [],
    }
    replay_a = replay_reasoning_execution_receipt(receipt=receipt)
    replay_b = replay_reasoning_execution_receipt(receipt=receipt)
    assert replay_a == replay_b


def test_replay_reasoning_execution_receipt_payload_reproduces_same_result():
    receipt = {
        "trace_id": "trace-3",
        "replay_token": "",
        "query": "Q",
        "answer": "A",
        "confidence_score": 0.6,
        "sources": [],
        "policy_decisions": [],
        "risk_flags": [],
    }
    payload = serialize_reasoning_execution_receipt(receipt=receipt)
    assert replay_reasoning_execution_receipt_payload(payload=payload) == replay_reasoning_execution_receipt(
        receipt=receipt
    )
