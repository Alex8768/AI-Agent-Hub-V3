from __future__ import annotations

from src.layers.pro.reasoning.contracts import (
    LLM_PLANNER_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
)
from src.services.answer.reasoning.llm_planner_policy import (
    build_deterministic_plan as _build_deterministic_plan_impl,
    build_planner_with_fallback as _build_planner_with_fallback_impl,
    infer_assistant_intent as _infer_assistant_intent_impl,
    parse_llm_planner_intent as _parse_llm_planner_intent_impl,
)

_LLM_PLANNER_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def infer_assistant_intent(*, query: str, assistant_mode_enabled: bool) -> dict[str, object]:
    return _infer_assistant_intent_impl(
        query=query,
        assistant_mode_enabled=assistant_mode_enabled,
    )


def build_deterministic_plan(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    return _build_deterministic_plan_impl(
        query=query,
        intent_payload=intent_payload,
        assistant_mode_enabled=assistant_mode_enabled,
        plan_contract_version=PLAN_CONTRACT_VERSION,
    )


def parse_llm_planner_intent(raw_text: str) -> str:
    return _parse_llm_planner_intent_impl(
        raw_text,
        allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
    )


async def build_planner_with_fallback(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
    llm: object | None,
    llm_enabled: bool,
    llm_model: str,
    llm_error: str,
    deterministic_plan_builder: object | None = None,
    parse_intent_fn: object | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return await _build_planner_with_fallback_impl(
        query=query,
        intent_payload=intent_payload,
        assistant_mode_enabled=assistant_mode_enabled,
        llm=llm,
        llm_enabled=llm_enabled,
        llm_model=llm_model,
        llm_error=llm_error,
        deterministic_plan_builder=deterministic_plan_builder or build_deterministic_plan,
        parse_intent_fn=parse_intent_fn or parse_llm_planner_intent,
        llm_planner_contract_version=LLM_PLANNER_CONTRACT_VERSION,
    )
