from __future__ import annotations

from fastapi import Request

from src.layers.pro.reasoning.contracts import (
    ADAPTATION_CONTRACT_VERSION,
    AnswerRequest,
    FEEDBACK_CONTRACT_VERSION,
    TOOL_SELECTION_CONTRACT_VERSION,
)
from src.services.answer.reasoning.llm_planner_policy import (
    build_feedback_adaptation_bundle as _build_feedback_adaptation_bundle_impl,
    build_feedback_learning_bundle as _build_feedback_learning_bundle_impl,
    build_tool_selection_bundle as _build_tool_selection_bundle_impl,
)

_LLM_PLANNER_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def build_feedback_learning_bundle(
    *,
    req: AnswerRequest,
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    return _build_feedback_learning_bundle_impl(
        req=req,
        assistant_mode_enabled=assistant_mode_enabled,
        feedback_contract_version=FEEDBACK_CONTRACT_VERSION,
    )


def build_feedback_adaptation_bundle(
    *,
    feedback_bundle: dict[str, object],
    intent_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    return _build_feedback_adaptation_bundle_impl(
        feedback_bundle=feedback_bundle,
        intent_bundle=intent_bundle,
        plan_bundle=plan_bundle,
        assistant_mode_enabled=assistant_mode_enabled,
        adaptation_contract_version=ADAPTATION_CONTRACT_VERSION,
        allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
    )


def build_tool_selection_bundle(
    *,
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    mcp_tools: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return _build_tool_selection_bundle_impl(
        plan_bundle=plan_bundle,
        assistant_mode_enabled=assistant_mode_enabled,
        mcp_tools=mcp_tools,
        tool_selection_contract_version=TOOL_SELECTION_CONTRACT_VERSION,
    )


def load_mcp_tools_from_runtime(http: Request) -> list[dict[str, object]]:
    state = getattr(getattr(http, "app", None), "state", None)
    registry = getattr(state, "mcp_registry", None) if state is not None else None
    if registry is None:
        return []
    try:
        list_tools = getattr(registry, "list_tools", None)
        if not callable(list_tools):
            return []
        rows = list(list_tools(enabled_only=True) or [])
        return [dict(row or {}) for row in rows]
    except Exception:
        return []
