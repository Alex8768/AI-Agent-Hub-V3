from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    ReasoningOptimizationProposal,
    build_reasoning_optimization_proposals,
)
from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    ReasoningOptimizationSignal,
    build_reasoning_optimization_signal,
)


class ReasoningOptimizationDecision(TypedDict):
    decision_id: str
    action: str
    selected_proposal_ids: list[str]
    reason_codes: list[str]
    confidence: float
    requires_human_review: bool


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_reasoning_optimization_decision(
    *,
    decision_id: object,
    action: object,
    selected_proposal_ids: object = None,
    reason_codes: object = None,
    confidence: object = 0.0,
    requires_human_review: object = False,
) -> ReasoningOptimizationDecision:
    """Build normalized optimization decision contract."""
    normalized_action = _normalize_string(action).lower() or "defer"
    if normalized_action not in {"approve", "reject", "defer"}:
        normalized_action = "defer"
    return {
        "decision_id": _normalize_string(decision_id),
        "action": normalized_action,
        "selected_proposal_ids": _normalize_string_list(selected_proposal_ids),
        "reason_codes": _normalize_string_list(reason_codes),
        "confidence": _normalize_float_01(confidence, default=0.0),
        "requires_human_review": bool(requires_human_review),
    }


def decide_reasoning_optimization_action(
    *,
    signal: ReasoningOptimizationSignal,
    proposals: list[ReasoningOptimizationProposal],
    decision_id: object = "optimization_decision",
) -> ReasoningOptimizationDecision:
    """Build deterministic optimization decision from signal and proposals."""
    normalized_signal = build_reasoning_optimization_signal(
        trace_id=signal.get("trace_id", ""),
        confidence_score=signal.get("confidence_score", 0.0),
        coverage_score=signal.get("coverage_score", 0.0),
        pass_rate=signal.get("pass_rate", 0.0),
        average_latency_ms=signal.get("average_latency_ms", 0),
        warnings_count=signal.get("warnings_count", 0),
        retry_rate=signal.get("retry_rate", 0.0),
        signal_tags=signal.get("signal_tags", []),
    )
    normalized_proposals = build_reasoning_optimization_proposals(
        proposals=[dict(x) for x in list(proposals or [])]
    )

    if not normalized_proposals:
        return build_reasoning_optimization_decision(
            decision_id=decision_id,
            action="defer",
            selected_proposal_ids=[],
            reason_codes=["no_proposals"],
            confidence=0.0,
            requires_human_review=False,
        )

    selected = [
        row for row in normalized_proposals
        if float(row.get("expected_gain", 0.0) or 0.0) > 0.0
    ]
    high_risk_present = any(
        str(row.get("risk_level", "") or "") in {"high", "critical"}
        for row in selected
    )

    confidence_floor = min(
        float(normalized_signal.get("confidence_score", 0.0) or 0.0),
        float(normalized_signal.get("pass_rate", 0.0) or 0.0),
    )

    if not selected:
        action = "reject"
        reason_codes = ["non_positive_expected_gain"]
    elif confidence_floor >= 0.6 and not high_risk_present:
        action = "approve"
        reason_codes = ["safe_gain_available"]
    else:
        action = "defer"
        reason_codes = ["requires_review"]
        if high_risk_present:
            reason_codes.append("high_risk_proposal")
        if confidence_floor < 0.6:
            reason_codes.append("low_signal_confidence")

    selected_ids = [str(row.get("proposal_id", "") or "") for row in selected]
    return build_reasoning_optimization_decision(
        decision_id=decision_id,
        action=action,
        selected_proposal_ids=selected_ids,
        reason_codes=reason_codes,
        confidence=confidence_floor,
        requires_human_review=bool(action == "defer"),
    )
