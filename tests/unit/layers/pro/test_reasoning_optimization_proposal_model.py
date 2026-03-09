from __future__ import annotations

from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    build_reasoning_optimization_proposal,
    build_reasoning_optimization_proposals,
)


def test_build_reasoning_optimization_proposal_normalizes_values():
    proposal = build_reasoning_optimization_proposal(
        proposal_id=" p-1 ",
        parameter=" retry_threshold ",
        current_value="0.7",
        proposed_value="1.3",
        expected_gain="-2.0",
        risk_level=" HIGH ",
        rationale=["reduce retries", " reduce retries ", ""],
    )
    assert proposal == {
        "proposal_id": "p-1",
        "parameter": "retry_threshold",
        "current_value": 0.7,
        "proposed_value": 1.0,
        "expected_gain": -1.0,
        "risk_level": "high",
        "rationale": ["reduce retries"],
    }


def test_build_reasoning_optimization_proposal_unknown_risk_defaults():
    proposal = build_reasoning_optimization_proposal(
        proposal_id="p-2",
        parameter="max_steps",
        current_value=0.4,
        proposed_value=0.5,
        expected_gain=0.2,
        risk_level="unsafe",
        rationale=[],
    )
    assert proposal["risk_level"] == "medium"


def test_build_reasoning_optimization_proposals_is_deterministic_and_filters_invalid():
    proposals = build_reasoning_optimization_proposals(
        proposals=[
            {
                "proposal_id": "b",
                "parameter": "max_latency",
                "current_value": 0.3,
                "proposed_value": 0.4,
                "expected_gain": 0.1,
            },
            {
                "proposal_id": " ",
                "parameter": "max_steps",
                "current_value": 0.2,
                "proposed_value": 0.3,
                "expected_gain": 0.1,
            },
            {
                "proposal_id": "a",
                "parameter": "max_steps",
                "current_value": 0.2,
                "proposed_value": 0.3,
                "expected_gain": 0.1,
            },
        ]
    )
    assert [row["proposal_id"] for row in proposals] == ["a", "b"]
