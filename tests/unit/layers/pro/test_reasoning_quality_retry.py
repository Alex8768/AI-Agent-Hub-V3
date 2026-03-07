from __future__ import annotations

from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry


def test_retry_policy_allows_single_retry_when_confidence_low():
    result = decide_reasoning_quality_retry(
        confidence_score=0.4,
        threshold=0.6,
        attempt=0,
        max_retries=1,
    )
    assert result["should_retry"] is True
    assert result["next_attempt"] == 1
    assert result["reason"] == "retry_allowed_low_confidence"
    assert result["loop_guard_triggered"] is False


def test_retry_policy_denies_when_budget_exhausted():
    result = decide_reasoning_quality_retry(
        confidence_score=0.3,
        threshold=0.6,
        attempt=1,
        max_retries=1,
    )
    assert result["should_retry"] is False
    assert result["next_attempt"] == 1
    assert result["reason"] == "retry_denied_budget_exhausted"
    assert result["loop_guard_triggered"] is True


def test_retry_policy_skips_when_confidence_is_sufficient():
    result = decide_reasoning_quality_retry(
        confidence_score=0.8,
        threshold=0.6,
        attempt=0,
        max_retries=1,
    )
    assert result["should_retry"] is False
    assert result["reason"] == "retry_not_needed_confidence_ok"
    assert result["loop_guard_triggered"] is False


def test_retry_policy_normalizes_invalid_input_bounds():
    result = decide_reasoning_quality_retry(
        confidence_score=2.0,
        threshold=-1.0,
        attempt=-5,
        max_retries=-3,
    )
    assert result["attempt"] == 0
    assert result["max_retries"] == 0
    assert result["confidence_score"] == 1.0
    assert result["threshold"] == 0.0
    assert result["should_retry"] is False
