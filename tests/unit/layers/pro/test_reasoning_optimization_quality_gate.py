from __future__ import annotations

from src.layers.pro.reasoning.engine import ReasoningEngine
from src.layers.pro.reasoning.optimization.optimization_decision_model import (
    decide_reasoning_optimization_action,
)
from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    build_reasoning_optimization_proposals,
)
from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    build_reasoning_optimization_signal_from_diagnostics,
)


def _diagnostics_payload() -> dict[str, object]:
    return {
        "trace_id": "trace-opt-1",
        "reasoning_quality": {
            "coverage": {"coverage_score": 0.5},
            "confidence": {"confidence_score": 0.4},
            "retry": {"should_retry": True},
        },
        "reasoning_benchmark": {
            "average_latency_ms": 120,
            "summary": {"pass_rate": 0.3},
        },
    }


def test_optimization_quality_gate_signal_and_proposals_are_deterministic():
    diagnostics = _diagnostics_payload()
    warnings = ["verify_warning"]

    signal_a = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics=diagnostics,
        warnings=warnings,
    )
    signal_b = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics=diagnostics,
        warnings=warnings,
    )
    assert signal_a == signal_b

    proposals_a = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "b",
                "parameter": "confidence_target",
                "current_value": 0.4,
                "proposed_value": 0.7,
                "expected_gain": 0.3,
                "risk_level": "medium",
                "rationale": ["low_confidence"],
            },
            {
                "proposal_id": "a",
                "parameter": "coverage_target",
                "current_value": 0.5,
                "proposed_value": 0.8,
                "expected_gain": 0.2,
                "risk_level": "low",
                "rationale": ["low_coverage"],
            },
        ]
    )
    proposals_b = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "b",
                "parameter": "confidence_target",
                "current_value": 0.4,
                "proposed_value": 0.7,
                "expected_gain": 0.3,
                "risk_level": "medium",
                "rationale": ["low_confidence"],
            },
            {
                "proposal_id": "a",
                "parameter": "coverage_target",
                "current_value": 0.5,
                "proposed_value": 0.8,
                "expected_gain": 0.2,
                "risk_level": "low",
                "rationale": ["low_coverage"],
            },
        ]
    )
    assert proposals_a == proposals_b


def test_optimization_quality_gate_decision_boundaries_are_stable():
    signal = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics=_diagnostics_payload(),
        warnings=["verify_warning"],
    )
    proposals = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "p-safe",
                "parameter": "coverage_target",
                "current_value": 0.5,
                "proposed_value": 0.7,
                "expected_gain": 0.2,
                "risk_level": "low",
            },
            {
                "proposal_id": "p-risk",
                "parameter": "retry_budget",
                "current_value": 1.0,
                "proposed_value": 0.5,
                "expected_gain": 0.4,
                "risk_level": "high",
            },
        ]
    )
    decision = decide_reasoning_optimization_action(
        signal=signal,
        proposals=proposals,
        decision_id="quality-gate",
    )
    assert decision["action"] == "defer"
    assert "requires_review" in decision["reason_codes"]
    assert "high_risk_proposal" in decision["reason_codes"]
    assert "low_signal_confidence" in decision["reason_codes"]


def test_optimization_quality_gate_runtime_contract_parity():
    diagnostics = _diagnostics_payload()
    runtime = ReasoningEngine._build_reasoning_optimization_diagnostics(
        diagnostics=diagnostics,
        warnings=["verify_warning"],
    )

    assert set(runtime.keys()) == {"signal", "proposals", "decision"}
    signal = dict(runtime["signal"])
    assert set(signal.keys()) == {
        "trace_id",
        "confidence_score",
        "coverage_score",
        "pass_rate",
        "average_latency_ms",
        "warnings_count",
        "retry_rate",
        "signal_tags",
    }
    assert isinstance(runtime["proposals"], list)
    decision = dict(runtime["decision"])
    assert set(decision.keys()) == {
        "decision_id",
        "action",
        "selected_proposal_ids",
        "reason_codes",
        "confidence",
        "requires_human_review",
    }


def test_optimization_quality_gate_runtime_matches_decision_engine():
    diagnostics = _diagnostics_payload()
    warnings = ["verify_warning", "self_check_warning"]
    runtime = ReasoningEngine._build_reasoning_optimization_diagnostics(
        diagnostics=diagnostics,
        warnings=warnings,
    )
    direct = decide_reasoning_optimization_action(
        signal=dict(runtime["signal"]),
        proposals=[dict(x) for x in list(runtime["proposals"])],
        decision_id=dict(runtime["decision"]).get("decision_id", "optimization_decision:runtime"),
    )
    assert dict(runtime["decision"]) == direct
