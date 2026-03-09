from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.multi_agent.coordination_model import (
    MultiAgentArbitrationDecision,
    build_multi_agent_arbitration_decision,
)


class MultiAgentArbitrationCandidate(TypedDict):
    agent_role: str
    answer: str
    score: float
    reasons: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_reasons(value: object) -> list[str]:
    reasons: list[str] = []
    for raw in list(value or []):
        text = _normalize_string(raw)
        if text:
            reasons.append(text)
    return reasons


def _normalize_candidates(
    candidates: list[dict[str, object]],
) -> list[MultiAgentArbitrationCandidate]:
    normalized: list[MultiAgentArbitrationCandidate] = []
    for raw in list(candidates or []):
        row = raw if isinstance(raw, dict) else {}
        answer = _normalize_string(row.get("answer", ""))
        role = _normalize_string(row.get("agent_role", ""))
        if not role or not answer:
            continue
        normalized.append(
            {
                "agent_role": role,
                "answer": answer,
                "score": _normalize_float_01(row.get("score", 0.0), default=0.0),
                "reasons": _normalize_reasons(row.get("reasons", [])),
            }
        )
    return normalized


def arbitrate_multi_agent_candidates(
    *,
    candidates: list[dict[str, object]],
    strategy: object = "highest_score",
) -> MultiAgentArbitrationDecision:
    """Build deterministic arbitration decision for candidate outputs."""
    strategy_name = _normalize_string(strategy) or "highest_score"
    normalized = _normalize_candidates(candidates)
    if not normalized:
        return build_multi_agent_arbitration_decision(
            winner_role="",
            strategy=strategy_name,
            reasons=["no_valid_candidates"],
            confidence_score=0.0,
        )

    # Deterministic: higher score first, then lexical role, then lexical answer.
    ranked = sorted(
        normalized,
        key=lambda row: (-float(row["score"]), str(row["agent_role"]), str(row["answer"])),
    )

    winner = ranked[0]
    winner_reasons = list(winner.get("reasons") or [])
    if strategy_name != "highest_score":
        winner_reasons.append("unsupported_strategy_fallback_to_highest_score")

    return build_multi_agent_arbitration_decision(
        winner_role=winner["agent_role"],
        strategy=strategy_name,
        reasons=winner_reasons,
        confidence_score=winner["score"],
    )
