from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.governance.receipt_model import ReasoningExecutionReceipt
from src.layers.pro.reasoning.governance.receipt_serializer import (
    deserialize_reasoning_execution_receipt,
    serialize_reasoning_execution_receipt,
)


def replay_reasoning_execution_receipt(*, receipt: dict[str, Any]) -> ReasoningExecutionReceipt:
    """Replay execution receipt via canonical serialization roundtrip."""
    payload = serialize_reasoning_execution_receipt(receipt=receipt)
    return deserialize_reasoning_execution_receipt(payload=payload)


def replay_reasoning_execution_receipt_payload(*, payload: str) -> ReasoningExecutionReceipt:
    """Replay execution receipt from serialized payload."""
    return deserialize_reasoning_execution_receipt(payload=payload)
