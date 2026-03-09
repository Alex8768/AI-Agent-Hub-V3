from __future__ import annotations

from src.layers.pro.reasoning.optimization.optimization_decision_model import (
    build_reasoning_optimization_decision,
    decide_reasoning_optimization_action,
)
from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    build_reasoning_optimization_proposals,
)
from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    build_reasoning_optimization_signal,
)


def test_build_reasoning_optimization_decision_normalizes_values():
    decision = build_reasoning_optimization_decision(
        decision_id=" d-1 ",
        action=" APPROVE ",
        selected_proposal_ids=["p-2", " p-1 ", "", "p-1"],
        reason_codes=["safe_gain_available", " safe_gain_available "],
        confidence="1.5",
        requires_human_review=0,
    )
    assert decision == {
        "decision_id": "d-1",
        "action": "approve",
        "selected_proposal_ids": ["p-1", "p-2"],
        "reason_codes": ["safe_gain_available"],
        "confidence": 1.0,
        "requires_human_review": False,
    }


def test_decide_reasoning_optimization_action_approves_safe_positive_gain():
    signal = build_reasoning_optimization_signal(
        trace_id="t1",
        confidence_score=0.9,
        coverage_score=0.8,
        pass_rate=0.85,
        average_latency_ms=100,
        warnings_count=0,
        retry_rate=0.0,
        signal_tags=[],
    )
    proposals = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "p1",
                "parameter": "max_steps",
                "current_value": 0.5,
                "proposed_value": 0.6,
                "expected_gain": 0.2,
                "risk_level": "low",
            }
        ]
    )
    decision = decide_reasoning_optimization_action(signal=signal, proposals=proposals)
    assert decision["action"] == "approve"
    assert decision["selected_proposal_ids"] == ["p1"]
    assert decision["requires_human_review"] is False


def test_decide_reasoning_optimization_action_defers_high_risk():
    signal = build_reasoning_optimization_signal(
        trace_id="t2",
        confidence_score=0.9,
        coverage_score=0.9,
        pass_rate=0.9,
        average_latency_ms=50,
        warnings_count=0,
        retry_rate=0.0,
        signal_tags=[],
    )
    proposals = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "p2",
                "parameter": "retry_rate",
                "current_value": 0.1,
                "proposed_value": 0.2,
                "expected_gain": 0.3,
                "risk_level": "critical",
            }
        ]
    )
    decision = decide_reasoning_optimization_action(signal=signal, proposals=proposals)
    assert decision["action"] == "defer"
    assert "high_risk_proposal" in decision["reason_codes"]
    assert decision["requires_human_review"] is True


def test_decide_reasoning_optimization_action_rejects_non_positive_gain():
    signal = build_reasoning_optimization_signal(
        trace_id="t3",
        confidence_score=0.7,
        coverage_score=0.7,
        pass_rate=0.7,
        average_latency_ms=80,
        warnings_count=0,
        retry_rate=0.0,
        signal_tags=[],
    )
    proposals = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "p3",
                "parameter": "latency_budget",
                "current_value": 0.4,
                "proposed_value": 0.5,
                "expected_gain": 0.0,
                "risk_level": "low",
            }
        ]
    )
    decision = decide_reasoning_optimization_action(signal=signal, proposals=proposals)
    assert decision["action"] == "reject"
    assert decision["reason_codes"] == ["non_positive_expected_gain"]
