"""Runtime context builder extracted from answer service."""

from __future__ import annotations


def build_answer_service_runtime_context(*, settings: object) -> dict[str, object]:
    return {
        "reasoning_enabled": bool(getattr(settings, "feature_reasoning", False)),
        "graphrag_enabled": bool(getattr(settings, "feature_graphrag", False)),
        "assistant_mode_enabled": bool(getattr(settings, "feature_assistant_mode", False)),
        "assistant_proactive_enabled": bool(getattr(settings, "feature_assistant_proactive", False)),
        "assistant_actions_enabled": bool(getattr(settings, "feature_assistant_actions", False)),
        "assistant_response_language": "auto",
    }
