from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.trace.trace_model import ReasoningTrace
from src.layers.pro.reasoning.trace.trace_serializer import (
    deserialize_reasoning_trace,
    serialize_reasoning_trace,
)


def replay_reasoning_trace(*, trace: dict[str, Any]) -> ReasoningTrace:
    """Replay reasoning trace via canonical serialization roundtrip."""
    payload = serialize_reasoning_trace(trace=trace)
    return deserialize_reasoning_trace(payload=payload)


def replay_reasoning_trace_payload(*, payload: str) -> ReasoningTrace:
    """Replay reasoning trace from serialized payload."""
    return deserialize_reasoning_trace(payload=payload)
