from __future__ import annotations

from typing import TypedDict


class ReasoningOptimizationProposal(TypedDict):
    proposal_id: str
    parameter: str
    current_value: float
    proposed_value: float
    expected_gain: float
    risk_level: str
    rationale: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float(value: object, *, default: float = 0.0, min_value: float = 0.0, max_value: float = 1.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(float(min_value), min(float(max_value), float(parsed)))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_reasoning_optimization_proposal(
    *,
    proposal_id: object,
    parameter: object,
    current_value: object,
    proposed_value: object,
    expected_gain: object,
    risk_level: object = "medium",
    rationale: object = None,
) -> ReasoningOptimizationProposal:
    """Build normalized optimization proposal contract."""
    risk = _normalize_string(risk_level).lower() or "medium"
    if risk not in {"low", "medium", "high", "critical"}:
        risk = "medium"
    return {
        "proposal_id": _normalize_string(proposal_id),
        "parameter": _normalize_string(parameter),
        "current_value": _normalize_float(current_value, default=0.0, min_value=0.0, max_value=1.0),
        "proposed_value": _normalize_float(proposed_value, default=0.0, min_value=0.0, max_value=1.0),
        "expected_gain": _normalize_float(expected_gain, default=0.0, min_value=-1.0, max_value=1.0),
        "risk_level": risk,
        "rationale": _normalize_string_list(rationale),
    }


def build_reasoning_optimization_proposals(
    *,
    proposals: list[dict[str, object]],
) -> list[ReasoningOptimizationProposal]:
    """Build deterministic list of optimization proposals."""
    rows: list[ReasoningOptimizationProposal] = []
    for raw in list(proposals or []):
        row = raw if isinstance(raw, dict) else {}
        proposal = build_reasoning_optimization_proposal(
            proposal_id=row.get("proposal_id", ""),
            parameter=row.get("parameter", ""),
            current_value=row.get("current_value", 0.0),
            proposed_value=row.get("proposed_value", 0.0),
            expected_gain=row.get("expected_gain", 0.0),
            risk_level=row.get("risk_level", "medium"),
            rationale=row.get("rationale", []),
        )
        if not proposal["proposal_id"] or not proposal["parameter"]:
            continue
        rows.append(proposal)
    rows.sort(key=lambda x: str(x["proposal_id"]))
    return rows
