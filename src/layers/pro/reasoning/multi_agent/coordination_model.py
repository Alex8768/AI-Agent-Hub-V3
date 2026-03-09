from __future__ import annotations

from typing import TypedDict


class MultiAgentCoordinationStep(TypedDict):
    step_index: int
    agent_role: str
    objective: str
    input_keys: list[str]
    output_key: str
    depends_on: list[int]


class MultiAgentCoordinationPlan(TypedDict):
    query: str
    steps: list[MultiAgentCoordinationStep]


class MultiAgentArbitrationDecision(TypedDict):
    winner_role: str
    strategy: str
    reasons: list[str]
    confidence_score: float


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(items: list[object]) -> list[str]:
    normalized: list[str] = []
    for raw in list(items or []):
        value = _normalize_string(raw)
        if not value:
            continue
        normalized.append(value)
    return normalized


def _normalize_index_list(items: list[object]) -> list[int]:
    normalized: list[int] = []
    for raw in list(items or []):
        try:
            parsed = int(raw)  # type: ignore[arg-type]
        except Exception:
            continue
        if parsed < 0:
            continue
        normalized.append(int(parsed))
    # deterministic de-duplication while preserving sorted order
    return sorted(set(normalized))


def build_multi_agent_coordination_step(
    *,
    step_index: object,
    agent_role: object,
    objective: object,
    input_keys: list[object],
    output_key: object,
    depends_on: list[object],
) -> MultiAgentCoordinationStep:
    """Build normalized multi-agent coordination step."""
    try:
        idx = int(step_index)  # type: ignore[arg-type]
    except Exception:
        idx = 0
    return {
        "step_index": max(0, int(idx)),
        "agent_role": _normalize_string(agent_role),
        "objective": _normalize_string(objective),
        "input_keys": _normalize_string_list(input_keys),
        "output_key": _normalize_string(output_key),
        "depends_on": _normalize_index_list(depends_on),
    }


def build_multi_agent_coordination_plan(
    *,
    query: object,
    steps: list[dict[str, object]],
) -> MultiAgentCoordinationPlan:
    """Build normalized coordination plan from raw step rows."""
    normalized_steps: list[MultiAgentCoordinationStep] = []
    for pos, raw in enumerate(list(steps or [])):
        row = raw if isinstance(raw, dict) else {}
        normalized_steps.append(
            build_multi_agent_coordination_step(
                step_index=row.get("step_index", pos),
                agent_role=row.get("agent_role", ""),
                objective=row.get("objective", ""),
                input_keys=list(row.get("input_keys") or []),
                output_key=row.get("output_key", ""),
                depends_on=list(row.get("depends_on") or []),
            )
        )
    return {
        "query": _normalize_string(query),
        "steps": normalized_steps,
    }


def build_multi_agent_arbitration_decision(
    *,
    winner_role: object,
    strategy: object,
    reasons: list[object],
    confidence_score: object,
) -> MultiAgentArbitrationDecision:
    """Build normalized arbitration decision for multi-agent outcomes."""
    return {
        "winner_role": _normalize_string(winner_role),
        "strategy": _normalize_string(strategy),
        "reasons": _normalize_string_list(reasons),
        "confidence_score": _normalize_float_01(confidence_score, default=0.0),
    }
