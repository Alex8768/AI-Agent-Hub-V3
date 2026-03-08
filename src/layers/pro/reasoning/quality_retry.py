from __future__ import annotations


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def decide_reasoning_quality_retry(
    *,
    confidence_score: float,
    attempt: int,
    threshold: float = 0.6,
    max_retries: int = 1,
) -> dict[str, object]:
    """Return deterministic retry decision with strict single-loop guard."""
    normalized_attempt = max(0, int(attempt))
    normalized_max_retries = max(0, int(max_retries))
    normalized_confidence = _clamp01(float(confidence_score))
    normalized_threshold = _clamp01(float(threshold))

    confidence_below_threshold = normalized_confidence < normalized_threshold
    retry_budget_available = normalized_attempt < normalized_max_retries
    should_retry = bool(confidence_below_threshold and retry_budget_available)

    if should_retry:
        reason = "retry_allowed_low_confidence"
    elif confidence_below_threshold and not retry_budget_available:
        reason = "retry_denied_budget_exhausted"
    else:
        reason = "retry_not_needed_confidence_ok"

    return {
        "attempt": normalized_attempt,
        "max_retries": normalized_max_retries,
        "confidence_score": normalized_confidence,
        "threshold": normalized_threshold,
        "confidence_below_threshold": confidence_below_threshold,
        "retry_budget_available": retry_budget_available,
        "should_retry": should_retry,
        "next_attempt": normalized_attempt + 1 if should_retry else normalized_attempt,
        "loop_guard_triggered": bool(confidence_below_threshold and not retry_budget_available),
        "reason": reason,
    }
