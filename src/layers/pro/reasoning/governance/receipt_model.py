from __future__ import annotations

from typing import TypedDict


class ExecutionReceiptSource(TypedDict):
    source_id: str
    source_type: str
    confidence: float


class ExecutionReceiptPolicyDecision(TypedDict):
    policy_name: str
    status: str
    reason: str


class ReasoningExecutionReceipt(TypedDict):
    version: str
    trace_id: str
    replay_token: str
    query: str
    answer: str
    confidence_score: float
    sources: list[ExecutionReceiptSource]
    policy_decisions: list[ExecutionReceiptPolicyDecision]
    risk_flags: list[str]


def _normalize_float_01(value: object, *, default: float = 0.0) -> float:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except Exception:
        parsed = float(default)
    return max(0.0, min(1.0, float(parsed)))


def _normalize_string_list(items: list[object]) -> list[str]:
    normalized: list[str] = []
    for raw in list(items or []):
        value = str(raw or "").strip()
        if not value:
            continue
        normalized.append(value)
    return normalized


def _normalize_sources(items: list[dict[str, object]]) -> list[ExecutionReceiptSource]:
    normalized: list[ExecutionReceiptSource] = []
    for raw in list(items or []):
        item = raw if isinstance(raw, dict) else {}
        source_id = str(item.get("source_id", "") or "").strip()
        source_type = str(item.get("source_type", "") or "").strip()
        if not source_id and not source_type:
            continue
        normalized.append(
            {
                "source_id": source_id,
                "source_type": source_type,
                "confidence": _normalize_float_01(item.get("confidence", 0.0), default=0.0),
            }
        )
    return normalized


def _normalize_policy_decisions(
    items: list[dict[str, object]],
) -> list[ExecutionReceiptPolicyDecision]:
    normalized: list[ExecutionReceiptPolicyDecision] = []
    for raw in list(items or []):
        item = raw if isinstance(raw, dict) else {}
        policy_name = str(item.get("policy_name", "") or "").strip()
        status = str(item.get("status", "") or "").strip()
        reason = str(item.get("reason", "") or "").strip()
        if not policy_name and not status and not reason:
            continue
        normalized.append(
            {
                "policy_name": policy_name,
                "status": status,
                "reason": reason,
            }
        )
    return normalized


def build_reasoning_execution_receipt(
    *,
    trace_id: str,
    replay_token: str,
    query: str,
    answer: str,
    confidence_score: float,
    sources: list[dict[str, object]],
    policy_decisions: list[dict[str, object]],
    risk_flags: list[object],
) -> ReasoningExecutionReceipt:
    """Build deterministic execution receipt for trust/governance flows."""
    return {
        "version": "v1",
        "trace_id": str(trace_id or "").strip(),
        "replay_token": str(replay_token or "").strip(),
        "query": str(query or "").strip(),
        "answer": str(answer or "").strip(),
        "confidence_score": _normalize_float_01(confidence_score, default=0.0),
        "sources": _normalize_sources(sources),
        "policy_decisions": _normalize_policy_decisions(policy_decisions),
        "risk_flags": _normalize_string_list(risk_flags),
    }
