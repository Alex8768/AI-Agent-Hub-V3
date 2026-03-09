from __future__ import annotations

from src.layers.pro.reasoning.governance.receipt_collector import (
    collect_reasoning_execution_receipt,
)


def test_collect_reasoning_execution_receipt_builds_expected_shape():
    receipt = collect_reasoning_execution_receipt(
        trace_id="trace-1",
        replay_token="replay-1",
        query="Q?",
        answer="A",
        diagnostics={
            "reasoning_quality": {"confidence": {"confidence_score": 0.9}},
            "top_evidence": ["chunk:c1", "memory:session:s1:last_answer"],
            "self_check": {"status": "pass", "reasons": []},
            "verify": {"status": "warn", "reasons": ["threshold"]},
            "reasoning_execution_policy": {
                "max_steps": 3,
                "max_retries": 1,
                "max_latency_ms": 15000,
            },
            "evidence_contract_valid_minimal": False,
        },
        warnings=["verify_warning"],
    )
    assert receipt["version"] == "v1"
    assert receipt["trace_id"] == "trace-1"
    assert receipt["replay_token"] == "replay-1"
    assert receipt["confidence_score"] == 0.9
    assert receipt["sources"] == [
        {"source_id": "c1", "source_type": "chunk", "confidence": 0.9},
        {"source_id": "session:s1:last_answer", "source_type": "memory", "confidence": 0.9},
    ]
    assert receipt["policy_decisions"] == [
        {"policy_name": "self_check", "status": "pass", "reason": ""},
        {"policy_name": "verify", "status": "warn", "reason": "threshold"},
        {
            "policy_name": "execution_policy",
            "status": "applied",
            "reason": "max_steps=3,max_retries=1,max_latency_ms=15000",
        },
    ]
    assert receipt["risk_flags"] == [
        "verify_warning",
        "verify_warn",
        "evidence_contract_minimal_invalid",
    ]


def test_collect_reasoning_execution_receipt_normalizes_values():
    receipt = collect_reasoning_execution_receipt(
        trace_id="  t  ",
        replay_token="  r  ",
        query="  q  ",
        answer="  a  ",
        diagnostics={
            "reasoning_quality": {"confidence": {"confidence_score": "1.7"}},
            "top_evidence": [" raw-source "],
            "self_check": {"status": " warn ", "reasons": ["  x  ", " "]},
            "verify": {"status": "", "reasons": []},
            "policy_decisions": [
                {"policy_name": "  custom  ", "status": "  pass  ", "reason": "  ok  "}
            ],
        },
        warnings=["  high_risk  ", " "],
    )
    assert receipt["trace_id"] == "t"
    assert receipt["replay_token"] == "r"
    assert receipt["query"] == "q"
    assert receipt["answer"] == "a"
    assert receipt["confidence_score"] == 1.0
    assert receipt["sources"] == [
        {"source_id": "raw-source", "source_type": "unknown", "confidence": 1.0}
    ]
    assert {"policy_name": "custom", "status": "pass", "reason": "ok"} in receipt["policy_decisions"]
    assert receipt["risk_flags"] == ["high_risk", "self_check_warn"]


def test_collect_reasoning_execution_receipt_handles_empty_inputs():
    receipt = collect_reasoning_execution_receipt(
        trace_id="",
        replay_token="",
        query="",
        answer="",
        diagnostics={},
        warnings=[],
    )
    assert receipt == {
        "version": "v1",
        "trace_id": "",
        "replay_token": "",
        "query": "",
        "answer": "",
        "confidence_score": 0.0,
        "sources": [],
        "policy_decisions": [
            {"policy_name": "self_check", "status": "", "reason": ""},
            {"policy_name": "verify", "status": "", "reason": ""},
        ],
        "risk_flags": [],
    }
