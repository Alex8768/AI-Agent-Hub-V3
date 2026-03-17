from __future__ import annotations

from src.services.answer.context.runtime_context import build_answer_service_runtime_context


def test_runtime_context_includes_agent_router_flag():
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        feature_agent_router_v1 = False

    context = build_answer_service_runtime_context(settings=_S())
    assert context["agent_router_v1_enabled"] is False

