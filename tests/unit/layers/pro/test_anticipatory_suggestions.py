from __future__ import annotations

from src.layers.pro.anticipatory.suggestions import (
    build_proactive_suggestion,
    build_proactive_suggestion_bundle,
    rank_proactive_suggestions,
)


def test_build_proactive_suggestion_normalizes_values() -> None:
    suggestion = build_proactive_suggestion(
        suggestion_id=" s1 ",
        suggestion_type="SUMMARIZATION",
        confidence=1.2,
        rationale=" r ",
        action_hint=" a ",
        source_signal_id=" sig ",
    )
    assert suggestion == {
        "suggestion_id": "s1",
        "suggestion_type": "summarization",
        "confidence": 1.0,
        "rationale": "r",
        "action_hint": "a",
        "source_signal_id": "sig",
    }


def test_rank_proactive_suggestions_is_deterministic() -> None:
    suggestions = [
        {
            "suggestion_id": "b",
            "suggestion_type": "follow_up",
            "confidence": 0.7,
            "rationale": "r2",
            "action_hint": "h2",
        },
        {
            "suggestion_id": "a",
            "suggestion_type": "automation",
            "confidence": 0.9,
            "rationale": "r1",
            "action_hint": "h1",
        },
    ]
    ranked_a = rank_proactive_suggestions(suggestions=suggestions, limit=3)
    ranked_b = rank_proactive_suggestions(suggestions=list(reversed(suggestions)), limit=3)
    assert ranked_a == ranked_b
    assert [x["suggestion_id"] for x in ranked_a] == ["a", "b"]


def test_build_proactive_suggestion_bundle_sets_active_status() -> None:
    bundle = build_proactive_suggestion_bundle(
        suggestions=[
            {
                "suggestion_id": "s2",
                "suggestion_type": "follow_up",
                "confidence": 0.6,
                "rationale": "r",
                "action_hint": "h",
            }
        ],
        limit=3,
        warnings=["w"],
    )
    assert bundle["status"] == "active"
    assert bundle["top_suggestion_id"] == "s2"
    assert bundle["reason_codes"] == ["suggestions_available"]
    assert bundle["warnings"] == ["w"]
