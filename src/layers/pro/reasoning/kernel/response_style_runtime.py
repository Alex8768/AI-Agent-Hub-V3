from __future__ import annotations

from typing import Callable


def build_reasoning_response_style_runtime() -> dict[str, Callable[..., object]]:
    """Build response-style runtime seam for assistant conversational UX."""
    from src.layers.pro.reasoning.response_style import (
        build_assistant_chat_recovery_answer,
        build_assistant_fallback_answer,
        is_generic_assistant_fallback_answer,
        is_simple_greeting_query,
        is_unknown_style_answer,
        normalize_low_evidence_friendliness,
    )

    return {
        "build_fallback_answer": build_assistant_fallback_answer,
        "build_chat_recovery_answer": build_assistant_chat_recovery_answer,
        "is_simple_greeting_query": is_simple_greeting_query,
        "is_unknown_style_answer": is_unknown_style_answer,
        "is_generic_assistant_fallback_answer": is_generic_assistant_fallback_answer,
        "normalize_low_evidence_friendliness": normalize_low_evidence_friendliness,
    }
