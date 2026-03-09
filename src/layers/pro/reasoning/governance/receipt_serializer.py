from __future__ import annotations

import json
from typing import Any

from src.layers.pro.reasoning.governance.receipt_model import (
    ReasoningExecutionReceipt,
    build_reasoning_execution_receipt,
)


def _default_replay_token(*, trace_id: str) -> str:
    normalized_trace_id = str(trace_id or "").strip()
    if not normalized_trace_id:
        return ""
    return f"replay:{normalized_trace_id}"


def _normalize_receipt_payload(payload: dict[str, Any]) -> ReasoningExecutionReceipt:
    row = payload if isinstance(payload, dict) else {}
    trace_id = str(row.get("trace_id", "") or "")
    replay_token_raw = str(row.get("replay_token", "") or "")
    replay_token = replay_token_raw or _default_replay_token(trace_id=trace_id)
    return build_reasoning_execution_receipt(
        trace_id=trace_id,
        replay_token=replay_token,
        query=str(row.get("query", "") or ""),
        answer=str(row.get("answer", "") or ""),
        confidence_score=float(row.get("confidence_score", 0.0) or 0.0),
        sources=list(row.get("sources") or []),
        policy_decisions=list(row.get("policy_decisions") or []),
        risk_flags=list(row.get("risk_flags") or []),
    )


def serialize_reasoning_execution_receipt(*, receipt: dict[str, Any]) -> str:
    """Serialize execution receipt into stable JSON representation."""
    normalized = _normalize_receipt_payload(receipt)
    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def deserialize_reasoning_execution_receipt(*, payload: str) -> ReasoningExecutionReceipt:
    """Deserialize JSON payload into normalized execution receipt contract."""
    parsed = json.loads(str(payload or "{}"))
    if not isinstance(parsed, dict):
        raise ValueError("Execution receipt payload must be a JSON object")
    return _normalize_receipt_payload(parsed)
