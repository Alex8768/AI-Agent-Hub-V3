from __future__ import annotations


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def compute_reasoning_quality_confidence(
    *,
    coverage_score: float,
    unsupported_claims: int,
    missing_claims: int,
    unsupported_penalty: float = 0.20,
    missing_penalty: float = 0.15,
    min_confidence_floor: float = 0.0,
) -> dict[str, float | int]:
    """Compute deterministic reasoning quality confidence.

    The model is intentionally simple and deterministic for A2.10 Patch 2:
    - start from lexical coverage score in [0, 1];
    - subtract fixed penalties for unsupported and missing claims;
    - clamp into [min_confidence_floor, 1.0].
    """
    base = _clamp01(float(coverage_score))
    unsupported_count = max(0, int(unsupported_claims))
    missing_count = max(0, int(missing_claims))

    penalty_unsupported = unsupported_count * float(unsupported_penalty)
    penalty_missing = missing_count * float(missing_penalty)
    total_penalty = penalty_unsupported + penalty_missing

    raw_confidence = base - total_penalty
    floor = _clamp01(float(min_confidence_floor))
    confidence = max(floor, _clamp01(raw_confidence))

    return {
        "coverage_score": base,
        "unsupported_claims": unsupported_count,
        "missing_claims": missing_count,
        "penalty_unsupported": penalty_unsupported,
        "penalty_missing": penalty_missing,
        "penalty_total": total_penalty,
        "raw_confidence": raw_confidence,
        "confidence_score": confidence,
    }
