from __future__ import annotations

from src.layers.pro.reasoning.multi_agent.arbitration_contract import (
    arbitrate_multi_agent_candidates,
)


def test_arbitrate_multi_agent_candidates_selects_highest_score():
    decision = arbitrate_multi_agent_candidates(
        candidates=[
            {
                "agent_role": "critic",
                "answer": "a",
                "score": 0.7,
                "reasons": ["coverage_ok"],
            },
            {
                "agent_role": "synthesizer",
                "answer": "b",
                "score": 0.92,
                "reasons": ["best_confidence"],
            },
        ],
    )
    assert decision == {
        "winner_role": "synthesizer",
        "strategy": "highest_score",
        "reasons": ["best_confidence"],
        "confidence_score": 0.92,
    }


def test_arbitrate_multi_agent_candidates_is_deterministic_on_tie():
    decision = arbitrate_multi_agent_candidates(
        candidates=[
            {
                "agent_role": "writer",
                "answer": "z-answer",
                "score": 0.8,
                "reasons": [],
            },
            {
                "agent_role": "critic",
                "answer": "a-answer",
                "score": 0.8,
                "reasons": [],
            },
        ],
    )
    assert decision["winner_role"] == "critic"
    assert decision["confidence_score"] == 0.8


def test_arbitrate_multi_agent_candidates_filters_invalid_rows():
    decision = arbitrate_multi_agent_candidates(
        candidates=[
            {"agent_role": "", "answer": "a", "score": 0.9, "reasons": []},
            {"agent_role": "critic", "answer": "", "score": 0.9, "reasons": []},
        ]
    )
    assert decision == {
        "winner_role": "",
        "strategy": "highest_score",
        "reasons": ["no_valid_candidates"],
        "confidence_score": 0.0,
    }


def test_arbitrate_multi_agent_candidates_unknown_strategy_fallback():
    decision = arbitrate_multi_agent_candidates(
        candidates=[
            {
                "agent_role": "critic",
                "answer": "a",
                "score": 0.95,
                "reasons": ["good"],
            }
        ],
        strategy="weighted_vote",
    )
    assert decision == {
        "winner_role": "critic",
        "strategy": "weighted_vote",
        "reasons": ["good", "unsupported_strategy_fallback_to_highest_score"],
        "confidence_score": 0.95,
    }
