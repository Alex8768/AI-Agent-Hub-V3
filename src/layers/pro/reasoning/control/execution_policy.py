from __future__ import annotations

from typing import TypedDict

DEFAULT_MAX_STEPS = 3
DEFAULT_MAX_LATENCY_MS = 15000
DEFAULT_MAX_RETRIES = 1

MAX_STEPS_CAP = 100
MAX_LATENCY_MS_CAP = 300000
MAX_RETRIES_CAP = 10


class ReasoningExecutionPolicy(TypedDict):
    max_steps: int
    max_latency_ms: int
    max_retries: int


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


def build_reasoning_execution_policy(
    *,
    max_steps: int | None = None,
    max_latency_ms: int | None = None,
    max_retries: int | None = None,
) -> ReasoningExecutionPolicy:
    """Build normalized execution policy with deterministic limits."""
    return {
        "max_steps": _normalize_int(
            max_steps,
            default=DEFAULT_MAX_STEPS,
            min_value=1,
            max_value=MAX_STEPS_CAP,
        ),
        "max_latency_ms": _normalize_int(
            max_latency_ms,
            default=DEFAULT_MAX_LATENCY_MS,
            min_value=1,
            max_value=MAX_LATENCY_MS_CAP,
        ),
        "max_retries": _normalize_int(
            max_retries,
            default=DEFAULT_MAX_RETRIES,
            min_value=0,
            max_value=MAX_RETRIES_CAP,
        ),
    }


def build_reasoning_execution_policy_from_dict(
    *,
    raw: dict[str, object] | None,
) -> ReasoningExecutionPolicy:
    payload = raw if isinstance(raw, dict) else {}
    return build_reasoning_execution_policy(
        max_steps=payload.get("max_steps"),
        max_latency_ms=payload.get("max_latency_ms"),
        max_retries=payload.get("max_retries"),
    )
