from __future__ import annotations

from typing import TypedDict

DEFAULT_MAX_VISITS_PER_SIGNATURE = 2
MAX_VISITS_PER_SIGNATURE_CAP = 1000


class ReasoningLoopGuardState(TypedDict):
    max_visits_per_signature: int
    seen_signatures: dict[str, int]


class ReasoningLoopGuardDecision(TypedDict):
    signature: str
    visit_count: int
    max_visits_per_signature: int
    should_stop: bool
    loop_guard_triggered: bool
    reason: str


class ReasoningLoopGuardCheckResult(TypedDict):
    state: ReasoningLoopGuardState
    decision: ReasoningLoopGuardDecision


def _normalize_int(
    value: object,
    *,
    default: int,
    min_value: int,
    max_value: int,
) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def _normalize_signature(value: object) -> str:
    normalized = " ".join(str(value or "").strip().split()).lower()
    return normalized if normalized else "__empty_step__"


def build_reasoning_loop_guard_state(
    *,
    max_visits_per_signature: int | None = None,
    seen_signatures: dict[str, object] | None = None,
) -> ReasoningLoopGuardState:
    normalized_max_visits = _normalize_int(
        max_visits_per_signature,
        default=DEFAULT_MAX_VISITS_PER_SIGNATURE,
        min_value=1,
        max_value=MAX_VISITS_PER_SIGNATURE_CAP,
    )
    normalized_seen: dict[str, int] = {}
    for raw_signature, raw_count in dict(seen_signatures or {}).items():
        signature = _normalize_signature(raw_signature)
        normalized_seen[signature] = _normalize_int(
            raw_count,
            default=0,
            min_value=0,
            max_value=MAX_VISITS_PER_SIGNATURE_CAP,
        )
    return {
        "max_visits_per_signature": normalized_max_visits,
        "seen_signatures": normalized_seen,
    }


def apply_reasoning_loop_guard(
    *,
    state: ReasoningLoopGuardState | None,
    step_description: object,
) -> ReasoningLoopGuardCheckResult:
    normalized_state = build_reasoning_loop_guard_state(
        max_visits_per_signature=(state or {}).get("max_visits_per_signature"),
        seen_signatures=(state or {}).get("seen_signatures"),  # type: ignore[arg-type]
    )
    signature = _normalize_signature(step_description)

    seen = dict(normalized_state["seen_signatures"])
    visit_count = int(seen.get(signature, 0)) + 1
    seen[signature] = int(visit_count)

    max_visits = int(normalized_state["max_visits_per_signature"])
    should_stop = bool(visit_count > max_visits)
    reason = (
        "loop_guard_stop_visit_limit_exceeded"
        if should_stop
        else "loop_guard_continue_within_budget"
    )
    return {
        "state": {
            "max_visits_per_signature": max_visits,
            "seen_signatures": seen,
        },
        "decision": {
            "signature": signature,
            "visit_count": int(visit_count),
            "max_visits_per_signature": max_visits,
            "should_stop": should_stop,
            "loop_guard_triggered": should_stop,
            "reason": reason,
        },
    }
