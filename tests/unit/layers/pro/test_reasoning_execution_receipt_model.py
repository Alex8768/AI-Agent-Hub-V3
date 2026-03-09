from __future__ import annotations

from src.layers.pro.reasoning.governance.receipt_model import (
    build_reasoning_execution_receipt,
)


def test_build_reasoning_execution_receipt_keeps_expected_contract_shape():
    receipt = build_reasoning_execution_receipt(
        trace_id="trace-1",
        replay_token="replay-1",
        query="What is capital of France?",
        answer="Paris.",
        confidence_score=0.95,
        sources=[
            {"source_id": "doc-1", "source_type": "chunk", "confidence": 0.9},
            {"source_id": "mem-1", "source_type": "memory", "confidence": 0.8},
        ],
        policy_decisions=[
            {"policy_name": "tool_write", "status": "allow", "reason": "read-only flow"},
        ],
        risk_flags=["none"],
    )
    assert receipt == {
        "version": "v1",
        "trace_id": "trace-1",
        "replay_token": "replay-1",
        "query": "What is capital of France?",
        "answer": "Paris.",
        "confidence_score": 0.95,
        "sources": [
            {"source_id": "doc-1", "source_type": "chunk", "confidence": 0.9},
            {"source_id": "mem-1", "source_type": "memory", "confidence": 0.8},
        ],
        "policy_decisions": [
            {"policy_name": "tool_write", "status": "allow", "reason": "read-only flow"},
        ],
        "risk_flags": ["none"],
    }


def test_build_reasoning_execution_receipt_normalizes_values_and_filters_empty_items():
    receipt = build_reasoning_execution_receipt(
        trace_id="  t  ",
        replay_token="  r  ",
        query="  q  ",
        answer="  a  ",
        confidence_score=2.7,
        sources=[
            {"source_id": "  doc-1  ", "source_type": "  chunk  ", "confidence": -5},
            {"source_id": "", "source_type": " ", "confidence": 0.5},
        ],
        policy_decisions=[
            {"policy_name": "  p1  ", "status": "  warn  ", "reason": "  bounded  "},
            {"policy_name": "", "status": " ", "reason": ""},
        ],
        risk_flags=["  high_latency  ", "", "   "],
    )
    assert receipt["trace_id"] == "t"
    assert receipt["replay_token"] == "r"
    assert receipt["query"] == "q"
    assert receipt["answer"] == "a"
    assert receipt["confidence_score"] == 1.0
    assert receipt["sources"] == [
        {"source_id": "doc-1", "source_type": "chunk", "confidence": 0.0}
    ]
    assert receipt["policy_decisions"] == [
        {"policy_name": "p1", "status": "warn", "reason": "bounded"}
    ]
    assert receipt["risk_flags"] == ["high_latency"]


def test_build_reasoning_execution_receipt_handles_empty_inputs_with_stable_defaults():
    receipt = build_reasoning_execution_receipt(
        trace_id="",
        replay_token="",
        query="",
        answer="",
        confidence_score=0.0,
        sources=[],
        policy_decisions=[],
        risk_flags=[],
    )
    assert receipt == {
        "version": "v1",
        "trace_id": "",
        "replay_token": "",
        "query": "",
        "answer": "",
        "confidence_score": 0.0,
        "sources": [],
        "policy_decisions": [],
        "risk_flags": [],
    }
