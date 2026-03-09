from __future__ import annotations

import pytest

from src.layers.pro.reasoning.governance.receipt_serializer import (
    deserialize_reasoning_execution_receipt,
    serialize_reasoning_execution_receipt,
)


def test_serialize_reasoning_execution_receipt_is_deterministic():
    receipt = {
        "trace_id": "trace-1",
        "replay_token": "replay-trace-1",
        "query": "Q",
        "answer": "A",
        "confidence_score": 0.9,
        "sources": [{"source_id": "c1", "source_type": "chunk", "confidence": 0.7}],
        "policy_decisions": [{"policy_name": "verify", "status": "pass", "reason": ""}],
        "risk_flags": ["none"],
    }
    payload_a = serialize_reasoning_execution_receipt(receipt=receipt)
    payload_b = serialize_reasoning_execution_receipt(receipt=receipt)
    assert payload_a == payload_b
    assert payload_a == (
        '{"answer":"A","confidence_score":0.9,'
        '"policy_decisions":[{"policy_name":"verify","reason":"","status":"pass"}],'
        '"query":"Q","replay_token":"replay-trace-1",'
        '"risk_flags":["none"],'
        '"sources":[{"confidence":0.7,"source_id":"c1","source_type":"chunk"}],'
        '"trace_id":"trace-1","version":"v1"}'
    )


def test_deserialize_reasoning_execution_receipt_normalizes_and_links_replay_token():
    payload = (
        '{"trace_id":"  t-1  ","replay_token":"",'
        '"query":"  Q  ","answer":"  A  ","confidence_score":2.0,'
        '"sources":[{"source_id":"  c1  ","source_type":" chunk ","confidence":-1}],'
        '"policy_decisions":[{"policy_name":" verify ","status":" warn ","reason":" x "}],'
        '"risk_flags":["  flag1  "," "]}'
    )
    receipt = deserialize_reasoning_execution_receipt(payload=payload)
    assert receipt == {
        "version": "v1",
        "trace_id": "t-1",
        "replay_token": "replay:t-1",
        "query": "Q",
        "answer": "A",
        "confidence_score": 1.0,
        "sources": [{"source_id": "c1", "source_type": "chunk", "confidence": 0.0}],
        "policy_decisions": [{"policy_name": "verify", "status": "warn", "reason": "x"}],
        "risk_flags": ["flag1"],
    }


def test_deserialize_reasoning_execution_receipt_rejects_non_object_json():
    with pytest.raises(ValueError, match="JSON object"):
        deserialize_reasoning_execution_receipt(payload='["not-an-object"]')
