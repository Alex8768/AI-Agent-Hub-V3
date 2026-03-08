from __future__ import annotations

import pytest

from src.layers.pro.reasoning.quality_confidence import compute_reasoning_quality_confidence


def test_compute_reasoning_quality_confidence_happy_path():
    result = compute_reasoning_quality_confidence(
        coverage_score=0.8,
        unsupported_claims=1,
        missing_claims=1,
        unsupported_penalty=0.2,
        missing_penalty=0.1,
    )
    assert result["coverage_score"] == 0.8
    assert result["penalty_total"] == pytest.approx(0.3)
    assert result["raw_confidence"] == pytest.approx(0.5)
    assert result["confidence_score"] == pytest.approx(0.5)


def test_compute_reasoning_quality_confidence_clamps_and_normalizes_counts():
    result = compute_reasoning_quality_confidence(
        coverage_score=1.7,
        unsupported_claims=-2,
        missing_claims=-1,
    )
    assert result["coverage_score"] == 1.0
    assert result["unsupported_claims"] == 0
    assert result["missing_claims"] == 0
    assert result["confidence_score"] == 1.0


def test_compute_reasoning_quality_confidence_respects_floor():
    result = compute_reasoning_quality_confidence(
        coverage_score=0.2,
        unsupported_claims=3,
        missing_claims=2,
        min_confidence_floor=0.1,
    )
    assert result["raw_confidence"] < 0.0
    assert result["confidence_score"] == 0.1
