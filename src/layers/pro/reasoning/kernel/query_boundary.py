from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest


def normalize_reasoning_query_input(query: str | AnswerRequest) -> str:
    """Normalize reasoning query input at planner/prompt boundary."""
    if isinstance(query, AnswerRequest):
        return str(query.query or "").strip()
    return str(query or "").strip()
