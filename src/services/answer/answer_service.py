from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import Request

from src.adapters.logging_adapter import get_logger
from src.layers.pro.anticipatory import (
    OpportunityScanner,
    WhisperRunner,
    build_proactive_suggestion_bundle,
)
from src.layers.pro.reasoning.execution_plane.request_boundary import (
    build_execution_request_boundary_bundle,
    normalize_execution_request,
)
from src.layers.pro.reasoning.kernel import build_reasoning_response_style_runtime
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.governance.subcore import build_governance_subcore_bundle
from src.layers.pro.reasoning.contracts import (
    APPROVAL_SESSION_CONTRACT_VERSION,
    ADAPTATION_CONTRACT_VERSION,
    AnswerRequest,
    DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    EVIDENCE_CONTRACT_VERSION,
    EXECUTION_PILOT_CONTRACT_VERSION,
    EXECUTION_RECEIPT_CONTRACT_VERSION,
    FEEDBACK_CONTRACT_VERSION,
    HANDSHAKE_CONTRACT_VERSION,
    IDEMPOTENCY_RECORD_CONTRACT_VERSION,
    INTENT_CONTRACT_VERSION,
    LLM_PLANNER_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
    TOOL_SELECTION_CONTRACT_VERSION,
    SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN,
    SELF_CHECK_MISSING_MINIMAL_COUNT_MAX,
    VERIFY_DIAGNOSTICS_VERSION,
    VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED,
    VERIFY_SELF_CHECK_REASONS_COUNT_MAX,
    VERIFY_SELF_CHECK_STATUS_REQUIRED,
)
from src.observability.request_context import get_request_id
from src.services.answer.interface_contract import (
    AnswerServiceRequestContract,
    build_answer_service_request_contract,
)
from src.services.answer.diagnostics_merge import (
    AnswerDiagnosticsMergeDeps,
    run_answer_diagnostics_merge_flow,
)
from src.services.answer.diagnostics.memory_consistency import (
    build_memory_consistency_bundle as _build_memory_consistency_bundle,
    build_memory_consistency_strategy_contract as _build_memory_consistency_strategy_contract,
)
from src.services.answer.diagnostics.reason_codes import (
    append_planning_reason_codes as _append_planning_reason_codes,
)
from src.services.answer.diagnostics.runtime_wiring import (
    wire_assistant_recovery_runtime_diagnostics as _wire_assistant_recovery_runtime_diagnostics,
    wire_feedback_adaptation_runtime_diagnostics as _wire_feedback_adaptation_runtime_diagnostics,
    wire_feedback_runtime_diagnostics as _wire_feedback_runtime_diagnostics,
    wire_planner_runtime_diagnostics as _wire_planner_runtime_diagnostics,
    wire_runtime_diagnostics as _wire_runtime_diagnostics,
    wire_tool_selection_runtime_diagnostics as _wire_tool_selection_runtime_diagnostics,
)
from src.services.answer.orchestrator import run_answer_orchestration_core
from src.services.answer.context.runtime_context import (
    build_answer_service_runtime_context as _build_answer_service_runtime_context,
)
from src.services.answer.context.session_text import clip_text as _clip_text
from src.services.answer.execution.durable_keys import (
    apply_durable_confirmation_token_guards as _apply_durable_confirmation_token_guards_impl,
    apply_execution_idempotency_guard as _apply_execution_idempotency_guard_impl,
    apply_handshake_transition as _apply_handshake_transition_impl,
    apply_handshake_transition_policy as _apply_handshake_transition_policy_impl,
    apply_rollback_contract_guard as _apply_rollback_contract_guard_impl,
    build_approval_session_bundle as _build_approval_session_bundle_impl,
    build_draft_action_bundle as _build_draft_action_bundle_impl,
    build_durable_approval_session_record as _build_durable_approval_session_record_impl,
    build_execution_handshake_bundle as _build_execution_handshake_bundle_impl,
    build_idempotency_record_snapshot as _build_idempotency_record_snapshot_impl,
    build_execution_pilot_bundle as _build_execution_pilot_bundle_impl,
    build_execution_receipt_stub as _build_execution_receipt_stub_impl,
    build_safe_mode_execution_gateway as _build_safe_mode_execution_gateway_impl,
    load_durable_records as _load_durable_records_impl,
    persist_durable_records as _persist_durable_records_impl,
    run_execution_pilot_runtime as _run_execution_pilot_runtime_impl,
)
from src.services.answer.observability.event_logger import log_observability
from src.services.answer.post_orchestration import (
    AnswerPostOrchestrationDeps,
    run_answer_post_orchestration_flow,
)
from src.services.answer.reasoning.runtime_adapter import (
    build_reasoning_runtime_adapter as _build_reasoning_runtime_adapter,
)
from src.services.answer.reasoning.llm_planner_policy import (
    apply_assistant_recovery_policy_guards as _apply_assistant_recovery_policy_guards_impl,
    apply_feedback_adaptation_policy_guards as _apply_feedback_adaptation_policy_guards,
    apply_feedback_policy_guards as _apply_feedback_policy_guards,
    apply_llm_planner_policy_guards as _apply_llm_planner_policy_guards,
    apply_plan_policy_guards as _apply_plan_policy_guards,
    apply_tool_selection_policy_guards as _apply_tool_selection_policy_guards,
    build_assistant_recovery_policy_contract as _build_assistant_recovery_policy_contract_impl,
    build_deterministic_plan as _build_deterministic_plan_impl,
    build_planner_with_fallback as _build_planner_with_fallback_impl,
    build_transition_policy_contract as _build_transition_policy_contract_impl,
    build_feedback_adaptation_policy_contract as _build_feedback_adaptation_policy_contract,
    build_feedback_learning_bundle as _build_feedback_learning_bundle_impl,
    build_feedback_policy_contract as _build_feedback_policy_contract,
    build_llm_planner_policy_contract as _build_llm_planner_policy_contract,
    build_tool_selection_bundle as _build_tool_selection_bundle_impl,
    build_tool_selection_policy_contract as _build_tool_selection_policy_contract,
    parse_llm_planner_intent as _parse_llm_planner_intent_impl,
)
from src.services.answer.response.language import (
    answer_language as _answer_language,
    detect_response_language as _detect_response_language,
    normalize_language_tag as _normalize_language_tag,
)
from src.services.answer.response_assembly import run_answer_response_assembly

EXECUTION_IDEMPOTENCY_CONTRACT_VERSION = "v1"
EXECUTION_GATEWAY_CONTRACT_VERSION = "v1"
EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES: tuple[str, ...] = (
    "prepare_summary_draft",
    "collect_context_draft",
    "prepare_workflow_draft",
)
EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN = "prepare_*_draft"
EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS = 1
_EXECUTION_IDEMPOTENCY_SEEN: dict[str, str] = {}
_LLM_PLANNER_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)
_LOGGER = get_logger()


class _AnswerFacadePipelineState:
    def __init__(
        self,
        *,
        resp: object,
        assistant_mode_enabled: bool,
        assistant_proactive_enabled: bool,
        assistant_actions_enabled: bool,
        assistant_response_language: str,
        loaded_durable_approval: dict[str, object],
        loaded_durable_idempotency: dict[str, object],
    ):
        self.resp = resp
        self.assistant_mode_enabled = bool(assistant_mode_enabled)
        self.assistant_proactive_enabled = bool(assistant_proactive_enabled)
        self.assistant_actions_enabled = bool(assistant_actions_enabled)
        self.assistant_response_language = str(assistant_response_language or "auto")
        self.loaded_durable_approval = dict(loaded_durable_approval or {})
        self.loaded_durable_idempotency = dict(loaded_durable_idempotency or {})


def _build_post_orchestration_deps() -> AnswerPostOrchestrationDeps:
    return AnswerPostOrchestrationDeps(
        run_anticipatory_safe_mode=_run_anticipatory_safe_mode,
        rank_proactive_bundle=_rank_proactive_bundle,
        build_draft_action_bundle=_build_draft_action_bundle,
        wire_runtime_diagnostics=_wire_runtime_diagnostics,
        bridge_plan_to_draft_actions=_bridge_plan_to_draft_actions,
        build_execution_handshake_bundle=_build_execution_handshake_bundle,
        build_transition_policy_contract=_build_transition_policy_contract,
        apply_handshake_transition_policy=_apply_handshake_transition_policy,
        extract_handshake_transition_input=_extract_handshake_transition_input,
        apply_durable_confirmation_token_guards=_apply_durable_confirmation_token_guards,
        apply_execution_idempotency_guard=_apply_execution_idempotency_guard,
        apply_handshake_transition=_apply_handshake_transition,
        apply_rollback_contract_guard=_apply_rollback_contract_guard,
        run_execution_pilot_runtime=_run_execution_pilot_runtime,
        build_execution_receipt_stub=_build_execution_receipt_stub,
        build_safe_mode_execution_gateway=_build_safe_mode_execution_gateway,
        build_execution_pilot_bundle=_build_execution_pilot_bundle,
        build_approval_session_bundle=_build_approval_session_bundle,
        build_durable_approval_session_record=_build_durable_approval_session_record,
        build_idempotency_record_snapshot=_build_idempotency_record_snapshot,
        append_planning_reason_codes=_append_planning_reason_codes,
        get_request_id=get_request_id,
        logger=_LOGGER,
        durable_approval_session_contract_version=DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
        idempotency_record_contract_version=IDEMPOTENCY_RECORD_CONTRACT_VERSION,
        execution_gateway_contract_version=EXECUTION_GATEWAY_CONTRACT_VERSION,
        execution_pilot_contract_version=EXECUTION_PILOT_CONTRACT_VERSION,
    )


def _build_diagnostics_merge_deps() -> AnswerDiagnosticsMergeDeps:
    return AnswerDiagnosticsMergeDeps(
        hydrate_durable_records_into_diagnostics=_hydrate_durable_records_into_diagnostics,
        persist_durable_records=_persist_durable_records,
        save_session_memory=_save_session_memory,
        append_planning_reason_codes=_append_planning_reason_codes,
        logger=_LOGGER,
    )


async def _run_answer_primary_pipeline(
    *,
    http: Request,
    req: object,
    workspace_id: str,
    settings: object,
    runtime_context: dict[str, object],
    engine: object,
    hybrid: object,
    get_reasoning_engine: object,
    get_memory_store: object,
) -> _AnswerFacadePipelineState:
    orchestration = await run_answer_orchestration_core(
        http=http,
        req=req,
        workspace_id=workspace_id,
        settings=settings,
        engine=engine,
        hybrid=hybrid,
        runtime_context=runtime_context,
        get_reasoning_engine=get_reasoning_engine,
        get_memory_store=get_memory_store,
        build_llm_adapter=_build_llm_adapter,
        load_session_memory=_load_session_memory,
        load_durable_records=_load_durable_records,
        retriever_adapter_cls=RetrieverAdapter,
        build_reasoning_runtime_adapter=_build_reasoning_runtime_adapter,
        detect_response_language=_detect_response_language,
        build_assistant_fallback_answer=_build_assistant_fallback_answer,
        apply_diagnostics=_apply_diagnostics,
    )
    resp = await run_answer_response_assembly(
        resp=orchestration.resp,
        req=req,
        llm=orchestration.llm,
        assistant_mode_enabled=bool(orchestration.assistant_mode_enabled),
        assistant_response_language=str(orchestration.assistant_response_language or "auto"),
        build_assistant_recovery_policy_contract=_build_assistant_recovery_policy_contract,
        apply_assistant_recovery_policy_guards=_apply_assistant_recovery_policy_guards,
        build_assistant_chat_recovery_answer=_build_assistant_chat_recovery_answer,
        normalize_low_evidence_friendliness=_normalize_low_evidence_friendliness,
        build_conversational_runtime_parity_bundle=_build_conversational_runtime_parity_bundle,
    )
    return _AnswerFacadePipelineState(
        resp=resp,
        assistant_mode_enabled=bool(orchestration.assistant_mode_enabled),
        assistant_proactive_enabled=bool(orchestration.assistant_proactive_enabled),
        assistant_actions_enabled=bool(orchestration.assistant_actions_enabled),
        assistant_response_language=str(orchestration.assistant_response_language or "auto"),
        loaded_durable_approval=dict(orchestration.loaded_durable_approval or {}),
        loaded_durable_idempotency=dict(orchestration.loaded_durable_idempotency or {}),
    )


def _build_planner_runtime_parity_fallback_bundle(*, diagnostics: dict[str, object]) -> dict[str, object]:
    diag = dict(diagnostics or {})
    planner_path_used = bool(diag.get("planner_path_used", False))
    action = str(diag.get("agent_current_action", "") or "").strip()
    step_idx = int(diag.get("agent_current_step", 0) or 0)
    trace = dict(diag.get("reasoning_trace") or {})
    plan_rows = list(trace.get("plan") or [])
    step_count = int(len(plan_rows))
    max_step_index = max(step_count - 1, 0)
    reason_codes: list[str] = ["planner_runtime_parity_evaluated"]
    status = "pass"
    if action:
        reason_codes.append("planner_runtime_action_present")
    else:
        status = "warn"
        reason_codes.append("planner_runtime_action_missing")
    if step_idx < 0 or (step_count > 0 and step_idx > max_step_index):
        status = "warn"
        reason_codes.append("planner_runtime_step_out_of_bounds")
    else:
        reason_codes.append("planner_runtime_step_in_bounds")
    reason_codes.append("planner_runtime_graph_path" if planner_path_used else "planner_runtime_fallback_path")
    return {
        "contract_version": "v1",
        "mode": "planner_runtime_parity_guarded",
        "status": status,
        "inputs": {
            "planner_path_used": planner_path_used,
            "planner_step_count": step_count,
            "observed_action": action,
            "observed_step": step_idx,
        },
        "thresholds": {
            "action_required": True,
            "step_index_min": 0,
            "step_index_max": int(max_step_index),
        },
        "reason_codes": sorted(set(reason_codes)),
    }


_RESPONSE_STYLE_RUNTIME = build_reasoning_response_style_runtime()
_build_assistant_fallback_answer = _RESPONSE_STYLE_RUNTIME["build_fallback_answer"]
_build_assistant_chat_recovery_answer = _RESPONSE_STYLE_RUNTIME["build_chat_recovery_answer"]
_is_simple_greeting_query = _RESPONSE_STYLE_RUNTIME["is_simple_greeting_query"]
_is_unknown_style_answer = _RESPONSE_STYLE_RUNTIME["is_unknown_style_answer"]
_is_generic_assistant_fallback_answer = _RESPONSE_STYLE_RUNTIME["is_generic_assistant_fallback_answer"]
_normalize_low_evidence_friendliness = _RESPONSE_STYLE_RUNTIME["normalize_low_evidence_friendliness"]


def _build_assistant_recovery_policy_contract() -> dict[str, object]:
    return _build_assistant_recovery_policy_contract_impl()


def _apply_assistant_recovery_policy_guards(
    *,
    policy_contract: dict[str, object],
    assistant_mode_enabled: bool,
    has_evidence: bool,
    plan_intent: str,
    query: str,
    target_language: str,
) -> tuple[bool, dict[str, object]]:
    return _apply_assistant_recovery_policy_guards_impl(
        policy_contract=policy_contract,
        assistant_mode_enabled=assistant_mode_enabled,
        has_evidence=has_evidence,
        plan_intent=plan_intent,
        query=query,
        target_language=target_language,
        normalize_language_tag_fn=_normalize_language_tag,
        is_simple_greeting_query_fn=_is_simple_greeting_query,
    )


def _rank_proactive_bundle(bundle: dict[str, object]) -> dict[str, object]:
    suggestions = [dict(row or {}) for row in list(bundle.get("suggestions") or [])]
    normalized: list[dict[str, object]] = []
    for row in suggestions:
        try:
            confidence = float(row.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        priority = int(round(confidence * 100))
        normalized.append(
            {
                **row,
                "priority": priority,
            }
        )

    normalized.sort(
        key=lambda x: (
            -int(x.get("priority", 0) or 0),
            str(x.get("suggestion_type", "") or ""),
            str(x.get("suggestion_id", "") or ""),
        )
    )
    ranked: list[dict[str, object]] = []
    for idx, row in enumerate(normalized, start=1):
        ranked.append(
            {
                **row,
                "rank": idx,
            }
        )

    reason_codes = sorted(
        set(
            [
                str(x)
                for x in list(bundle.get("reason_codes") or [])
                if str(x or "").strip()
            ]
            + (["ranked_by_priority"] if ranked else [])
        )
    )
    top_suggestion_id = str((ranked[0] or {}).get("suggestion_id", "") or "") if ranked else ""
    status = "active" if ranked else str(bundle.get("status", "idle") or "idle")
    return {
        "status": status,
        "suggestions": ranked,
        "top_suggestion_id": top_suggestion_id,
        "reason_codes": reason_codes,
        "warnings": list(bundle.get("warnings") or []),
    }


def _build_draft_action_bundle(
    *,
    proactive_bundle: dict[str, object],
    language: str,
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_draft_action_bundle_impl(
        proactive_bundle=proactive_bundle,
        language=language,
        actions_enabled=actions_enabled,
    )


def _infer_assistant_intent(*, query: str, assistant_mode_enabled: bool) -> dict[str, object]:
    text = str(query or "").strip()
    lowered = text.lower()

    if not assistant_mode_enabled:
        return {
            "intent": "disabled",
            "confidence": 0.0,
            "entities": {},
            "implicit_tasks": [],
            "source": "heuristic",
            "reason_codes": ["assistant_mode_disabled"],
        }

    if "проект" in lowered or "project" in lowered:
        return {
            "intent": "start_project",
            "confidence": 0.8,
            "entities": {"project_name": text[:120]},
            "implicit_tasks": [
                "project_workspace",
                "timeline_alignment",
                "contacts_research",
            ],
            "source": "heuristic",
            "reason_codes": ["keyword_project"],
        }
    if "встреч" in lowered or "митинг" in lowered or "meeting" in lowered:
        return {
            "intent": "prepare_meeting",
            "confidence": 0.7,
            "entities": {},
            "implicit_tasks": ["agenda_draft", "context_summary", "follow_up_tasks"],
            "source": "heuristic",
            "reason_codes": ["keyword_meeting"],
        }
    if "привет" in lowered or lowered.startswith("hi") or "hello" in lowered:
        return {
            "intent": "general_chat",
            "confidence": 0.6,
            "entities": {},
            "implicit_tasks": ["friendly_response"],
            "source": "heuristic",
            "reason_codes": ["keyword_greeting"],
        }
    return {
        "intent": "general_query",
        "confidence": 0.4,
        "entities": {},
        "implicit_tasks": [],
        "source": "heuristic",
        "reason_codes": ["fallback_general_query"],
    }


def _build_deterministic_plan(
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


def _parse_llm_planner_intent(raw_text: str) -> str:
    return _parse_llm_planner_intent_impl(
        raw_text,
        allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
    )


async def _build_planner_with_fallback(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
    llm: object | None,
    llm_enabled: bool,
    llm_model: str,
    llm_error: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return await _build_planner_with_fallback_impl(
        query=query,
        intent_payload=intent_payload,
        assistant_mode_enabled=assistant_mode_enabled,
        llm=llm,
        llm_enabled=llm_enabled,
        llm_model=llm_model,
        llm_error=llm_error,
        deterministic_plan_builder=_build_deterministic_plan,
        parse_intent_fn=_parse_llm_planner_intent,
        llm_planner_contract_version=LLM_PLANNER_CONTRACT_VERSION,
    )


def _build_conversational_runtime_parity_bundle(
    *,
    diagnostics: dict[str, object],
    query: str,
    answer: str,
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    query_text = str(query or "")
    answer_text = str(answer or "")
    assistant_mode_enabled = bool(diag.get("assistant_mode_enabled", False))
    response_mode = str(diag.get("response_mode", "") or "")
    response_language = _normalize_language_tag(
        str(diag.get("response_language", "auto") or "auto"),
        query=query_text,
    )
    answer_language = _answer_language(answer_text)
    has_evidence = int(diag.get("retrieved_provenance_count", 0) or 0) > 0
    unknown_style = _is_unknown_style_answer(answer_text)
    recovery_applied = bool(diag.get("assistant_chat_recovery_applied", False))
    friendliness_applied = "assistant_low_evidence_friendliness_applied" in {
        str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()
    }
    reason_codes: list[str] = ["conversational_runtime_parity_evaluated"]
    status = "pass"
    if assistant_mode_enabled:
        reason_codes.append("conversational_runtime_assistant_enabled")
    else:
        reason_codes.append("conversational_runtime_assistant_disabled")
    if answer_language == response_language:
        reason_codes.append("conversational_runtime_language_aligned")
    else:
        status = "warn"
        reason_codes.append("conversational_runtime_language_mismatch")
    if assistant_mode_enabled and not has_evidence and unknown_style:
        status = "warn"
        reason_codes.append("conversational_runtime_low_evidence_unknown_style")
    else:
        reason_codes.append("conversational_runtime_low_evidence_style_ok")
    if recovery_applied:
        reason_codes.append("conversational_runtime_recovery_applied")
    if friendliness_applied:
        reason_codes.append("conversational_runtime_friendliness_applied")
    return {
        "contract_version": "v1",
        "mode": "conversational_runtime_parity_guarded",
        "status": status,
        "inputs": {
            "assistant_mode_enabled": assistant_mode_enabled,
            "response_mode": response_mode,
            "response_language": response_language,
            "answer_language": answer_language,
            "has_evidence": has_evidence,
            "unknown_style_answer": unknown_style,
            "recovery_applied": recovery_applied,
            "friendliness_applied": friendliness_applied,
        },
        "thresholds": {
            "require_language_alignment": True,
            "require_non_unknown_style_when_low_evidence": True,
        },
        "reason_codes": sorted(set(reason_codes)),
    }


def _build_feedback_learning_bundle(
    *,
    req: AnswerRequest,
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    return _build_feedback_learning_bundle_impl(
        req=req,
        assistant_mode_enabled=assistant_mode_enabled,
        feedback_contract_version=FEEDBACK_CONTRACT_VERSION,
    )


def _build_feedback_adaptation_bundle(
    *,
    feedback_bundle: dict[str, object],
    intent_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": ADAPTATION_CONTRACT_VERSION,
            "mode": "feedback_to_planning_adaptation",
            "status": "disabled",
            "source": "deterministic",
            "latest_signal": "none",
            "boosted_intents": [],
            "suppressed_intents": [],
            "reason_codes": ["assistant_mode_disabled"],
        }

    feedback = dict(feedback_bundle or {})
    intent = dict(intent_bundle or {})
    plan = dict(plan_bundle or {})
    latest = str(feedback.get("latest_signal", "none") or "none").strip().lower()
    if latest not in {"approve", "cancel", "edit"}:
        latest = "none"

    reason_codes = ["feedback_adaptation_contract_baseline_built"]
    status = "ready"
    current_intent = str(intent.get("intent", "") or plan.get("intent", "") or "general_query").strip()
    if not current_intent:
        current_intent = "general_query"
    if current_intent not in _LLM_PLANNER_ALLOWED_INTENTS:
        current_intent = "general_query"
    boosted_intents: list[str] = []
    suppressed_intents: list[str] = []
    if latest == "none":
        status = "idle"
        reason_codes = ["feedback_adaptation_no_signal"]
    elif latest == "approve":
        boosted_intents = [current_intent]
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked", f"feedback_adaptation_boosted:{current_intent}"]
    elif latest == "cancel":
        boosted_intents = ["general_query"]
        if current_intent != "general_query":
            suppressed_intents = [current_intent]
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked", "feedback_adaptation_boosted:general_query"]
        if suppressed_intents:
            reason_codes.append(f"feedback_adaptation_suppressed:{suppressed_intents[0]}")
    elif latest == "edit":
        boosted_intents = [current_intent]
        if current_intent != "prepare_meeting":
            boosted_intents.append("prepare_meeting")
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked"]
        reason_codes.extend([f"feedback_adaptation_boosted:{x}" for x in boosted_intents])

    return {
        "contract_version": ADAPTATION_CONTRACT_VERSION,
        "mode": "feedback_to_planning_adaptation",
        "status": status,
        "source": "deterministic",
        "latest_signal": latest,
        "boosted_intents": boosted_intents,
        "suppressed_intents": suppressed_intents,
        "reason_codes": reason_codes,
    }


def _build_tool_selection_bundle(
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


def _load_mcp_tools_from_runtime(http: Request) -> list[dict[str, object]]:
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


def _bridge_plan_to_draft_actions(
    *,
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    language: str,
    actions_enabled: bool,
) -> dict[str, object]:
    if not actions_enabled:
        return dict(draft_actions_bundle or {})

    current = dict(draft_actions_bundle or {})
    existing_actions = list(current.get("actions") or [])
    if existing_actions:
        return current

    steps = [dict(step or {}) for step in list(plan_bundle.get("steps") or [])]
    if not steps:
        return current

    plan_id = str(plan_bundle.get("plan_id", "") or "")
    bridged_actions: list[dict[str, object]] = []
    for idx, step in enumerate(steps, start=1):
        step_id = str(step.get("step_id", "") or f"step:{idx}")
        step_action = str(step.get("action", "prepare_step_draft") or "prepare_step_draft")
        step_role = str(step.get("role", "assistant") or "assistant")
        if language == "ru":
            summary = f"Черновик шага плана: {step_action} ({step_role})."
            rollback = "Откат не требуется: создан только черновик шага."
        else:
            summary = f"Draft plan step prepared: {step_action} ({step_role})."
            rollback = "No rollback required: draft-only plan step."
        bridged_actions.append(
            {
                "action_id": f"draft_action:{plan_id}:{step_id}" if plan_id else f"draft_action:{step_id}",
                "action_type": "prepare_plan_step_draft",
                "status": "draft",
                "requires_confirmation": True,
                "estimated_impact": "low",
                "parameters": {
                    "plan_id": plan_id,
                    "step_id": step_id,
                    "role": step_role,
                    "action": step_action,
                },
                "preview": {
                    "title": step_action,
                    "summary": summary,
                    "rank": idx,
                },
                "rollback_plan": rollback,
            }
        )

    reason_codes = sorted(
        set([str(x) for x in list(current.get("reason_codes") or []) if str(x or "").strip()])
        | {"draft_actions_from_plan_bridge"}
    )
    return {
        "status": "ready",
        "actions": bridged_actions,
        "top_action_id": str((bridged_actions[0] or {}).get("action_id", "") or ""),
        "requires_confirmation": bool(bridged_actions),
        "reason_codes": reason_codes,
        "warnings": list(current.get("warnings") or []),
    }


def _build_execution_handshake_bundle(
    *,
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_execution_handshake_bundle_impl(
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions_bundle,
        assistant_mode_enabled=assistant_mode_enabled,
        actions_enabled=actions_enabled,
        handshake_contract_version=HANDSHAKE_CONTRACT_VERSION,
    )


def _extract_handshake_transition_input(req: AnswerRequest) -> dict[str, object]:
    filters = dict(getattr(req, "filters", {}) or {})
    return normalize_execution_request(filters=filters)


def _apply_handshake_transition(
    *,
    handshake_bundle: dict[str, object],
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> dict[str, object]:
    return _apply_handshake_transition_impl(
        handshake_bundle=handshake_bundle,
        transition_input=transition_input,
        draft_actions_bundle=draft_actions_bundle,
    )


def _apply_execution_idempotency_guard(
    *,
    transition_input: dict[str, object],
    workspace_id: str,
    plan_id: str,
    prior_record: dict[str, object] | None = None,
    persist: bool = True,
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_execution_idempotency_guard_impl(
        transition_input=transition_input,
        workspace_id=workspace_id,
        plan_id=plan_id,
        prior_record=prior_record,
        persist=persist,
        execution_idempotency_contract_version=EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
        seen_store=_EXECUTION_IDEMPOTENCY_SEEN,
    )


def _build_transition_policy_contract() -> dict[str, object]:
    return _build_transition_policy_contract_impl(
        max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        allowlisted_action_pattern=EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN,
    )


def _is_allowlisted_pilot_action_type(action_type: str, allowlisted_action_types: set[str]) -> bool:
    normalized = str(action_type or "").strip()
    if not normalized:
        return False
    if normalized in allowlisted_action_types:
        return True
    return normalized.startswith("prepare_") and normalized.endswith("_draft")


def _apply_handshake_transition_policy(
    *,
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_handshake_transition_policy_impl(
        transition_input=transition_input,
        draft_actions_bundle=draft_actions_bundle,
        policy_contract=policy_contract,
        is_allowlisted_action_type_fn=_is_allowlisted_pilot_action_type,
    )


def _apply_durable_confirmation_token_guards(
    *,
    transition_input: dict[str, object],
    durable_approval_record: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    return _apply_durable_confirmation_token_guards_impl(
        transition_input=transition_input,
        durable_approval_record=durable_approval_record,
    )


def _apply_rollback_contract_guard(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    return _apply_rollback_contract_guard_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
    )


def _run_execution_pilot_runtime(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    actions_enabled: bool,
) -> tuple[list[str], list[str]]:
    return _run_execution_pilot_runtime_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
        actions_enabled=actions_enabled,
        execution_pilot_allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        execution_pilot_max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        is_allowlisted_action_type_fn=_is_allowlisted_pilot_action_type,
    )


def _build_execution_receipt_stub(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
    executed_action_ids: list[str] | None = None,
) -> dict[str, object]:
    return _build_execution_receipt_stub_impl(
        handshake_bundle=handshake_bundle,
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions_bundle,
        workspace_id=workspace_id,
        request_id=request_id,
        executed_action_ids=executed_action_ids,
        execution_receipt_contract_version=EXECUTION_RECEIPT_CONTRACT_VERSION,
    )


def _build_safe_mode_execution_gateway(
    *,
    handshake_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_safe_mode_execution_gateway_impl(
        handshake_bundle=handshake_bundle,
        receipt_bundle=receipt_bundle,
        actions_enabled=actions_enabled,
        execution_gateway_contract_version=EXECUTION_GATEWAY_CONTRACT_VERSION,
    )


def _build_execution_pilot_bundle(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    return _build_execution_pilot_bundle_impl(
        handshake_bundle=handshake_bundle,
        draft_actions_bundle=draft_actions_bundle,
        receipt_bundle=receipt_bundle,
        actions_enabled=actions_enabled,
        execution_pilot_contract_version=EXECUTION_PILOT_CONTRACT_VERSION,
        execution_pilot_allowlisted_action_types=EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES,
        execution_pilot_max_approved_action_ids=EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        is_allowlisted_action_type_fn=_is_allowlisted_pilot_action_type,
    )


def _build_approval_session_bundle(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
) -> dict[str, object]:
    return _build_approval_session_bundle_impl(
        handshake_bundle=handshake_bundle,
        plan_bundle=plan_bundle,
        workspace_id=workspace_id,
        request_id=request_id,
        approval_session_contract_version=APPROVAL_SESSION_CONTRACT_VERSION,
    )


def _build_durable_approval_session_record(
    *,
    approval_session_bundle: dict[str, object],
    session_id: str,
    confirmation_token: str,
    transition_input: dict[str, object],
    previous_record: dict[str, object] | None = None,
) -> dict[str, object]:
    return _build_durable_approval_session_record_impl(
        approval_session_bundle=approval_session_bundle,
        session_id=session_id,
        confirmation_token=confirmation_token,
        transition_input=transition_input,
        previous_record=previous_record,
        durable_approval_session_contract_version=DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    )


def _build_idempotency_record_snapshot(
    *,
    execution_idempotency_bundle: dict[str, object],
    workspace_id: str,
    plan_id: str,
    transition_input: dict[str, object],
) -> dict[str, object]:
    return _build_idempotency_record_snapshot_impl(
        execution_idempotency_bundle=execution_idempotency_bundle,
        workspace_id=workspace_id,
        plan_id=plan_id,
        transition_input=transition_input,
        idempotency_record_contract_version=IDEMPOTENCY_RECORD_CONTRACT_VERSION,
    )


async def _load_durable_records(
    *,
    req: AnswerRequest,
    workspace_id: str,
    get_memory_store: object,
) -> tuple[dict[str, object], dict[str, object]]:
    return await _load_durable_records_impl(
        req=req,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )


def _hydrate_durable_records_into_diagnostics(
    *,
    diagnostics: dict[str, object],
    loaded_approval: dict[str, object],
    loaded_idempotency: dict[str, object],
) -> None:
    current_approval = dict(diagnostics.get("assistant_durable_approval_session") or {})
    current_idem = dict(diagnostics.get("assistant_idempotency_record") or {})
    if loaded_approval and not str(current_approval.get("approval_id", "") or ""):
        reasons = sorted(
            set([str(x) for x in list(loaded_approval.get("reason_codes") or []) if str(x)] + ["loaded_from_durable_store"])
        )
        diagnostics["assistant_durable_approval_session"] = {
            **loaded_approval,
            "reason_codes": reasons,
        }
    if loaded_idempotency and not str(current_idem.get("idempotency_key", "") or ""):
        reasons = sorted(
            set([str(x) for x in list(loaded_idempotency.get("reason_codes") or []) if str(x)] + ["loaded_from_durable_store"])
        )
        diagnostics["assistant_idempotency_record"] = {
            **loaded_idempotency,
            "reason_codes": reasons,
        }


async def _persist_durable_records(
    *,
    req: AnswerRequest,
    resp: object,
    workspace_id: str,
    get_memory_store: object,
) -> None:
    await _persist_durable_records_impl(
        req=req,
        resp=resp,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )


def _run_assistant_execution_orchestration_seam(
    *,
    req: AnswerRequest,
    diagnostics: dict[str, object],
    plan_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
    assistant_mode_enabled: bool,
    assistant_actions_enabled: bool,
) -> dict[str, object]:
    anticipatory = dict(diagnostics.get("anticipatory") or {})
    draft_actions = dict(anticipatory.get("draft_actions") or {})
    handshake = _build_execution_handshake_bundle(
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions,
        assistant_mode_enabled=assistant_mode_enabled,
        actions_enabled=assistant_actions_enabled,
    )
    transition_policy = _build_transition_policy_contract()
    transition_input, transition_policy_eval = _apply_handshake_transition_policy(
        transition_input=_extract_handshake_transition_input(req),
        draft_actions_bundle=draft_actions,
        policy_contract=transition_policy,
    )
    execution_request_boundary = build_execution_request_boundary_bundle(
        execution_request=transition_input,
        transition_policy=transition_policy_eval,
    )
    transition_input, execution_idempotency = _apply_execution_idempotency_guard(
        transition_input=transition_input,
        workspace_id=str(workspace_id or ""),
        plan_id=str(plan_bundle.get("plan_id", "") or ""),
        persist=False,
    )
    handshake = _apply_handshake_transition(
        handshake_bundle=handshake,
        transition_input=transition_input,
        draft_actions_bundle=draft_actions,
    )
    handshake, rollback_contract_eval = _apply_rollback_contract_guard(
        handshake_bundle=handshake,
        draft_actions_bundle=draft_actions,
    )
    transition_policy_eval["rollback_contract_status"] = str(
        rollback_contract_eval.get("status", "not_evaluated") or "not_evaluated"
    )
    transition_policy_eval["rollback_missing_action_ids"] = [
        str(x) for x in list(rollback_contract_eval.get("rollback_missing_action_ids") or []) if str(x)
    ]
    transition_policy_eval["applied_reason_codes"] = sorted(
        set(
            [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
            + [str(x) for x in list(rollback_contract_eval.get("reason_codes") or []) if str(x)]
        )
    )
    executed_action_ids, pilot_runtime_reasons = _run_execution_pilot_runtime(
        handshake_bundle=handshake,
        draft_actions_bundle=draft_actions,
        actions_enabled=assistant_actions_enabled,
    )
    transition_policy_eval["applied_reason_codes"] = sorted(
        set(
            [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
            + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
        )
    )
    receipt = _build_execution_receipt_stub(
        handshake_bundle=handshake,
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions,
        workspace_id=str(workspace_id or ""),
        request_id=str(request_id or ""),
        executed_action_ids=executed_action_ids,
    )
    execution_gateway = _build_safe_mode_execution_gateway(
        handshake_bundle=handshake,
        receipt_bundle=receipt,
        actions_enabled=assistant_actions_enabled,
    )
    execution_pilot = _build_execution_pilot_bundle(
        handshake_bundle=handshake,
        draft_actions_bundle=draft_actions,
        receipt_bundle=receipt,
        actions_enabled=assistant_actions_enabled,
    )
    approval_session = _build_approval_session_bundle(
        handshake_bundle=handshake,
        plan_bundle=plan_bundle,
        workspace_id=str(workspace_id or ""),
        request_id=str(request_id or ""),
    )
    durable_approval_record = _build_durable_approval_session_record(
        approval_session_bundle=approval_session,
        session_id=str(getattr(req, "session_id", "") or "default"),
        confirmation_token=str(handshake.get("confirmation_token", "") or ""),
        transition_input=transition_input,
        previous_record={},
    )
    idempotency_record = _build_idempotency_record_snapshot(
        execution_idempotency_bundle=execution_idempotency,
        workspace_id=str(workspace_id or ""),
        plan_id=str(plan_bundle.get("plan_id", "") or ""),
        transition_input=transition_input,
    )
    return {
        "handshake": handshake,
        "execution_transition_policy": transition_policy_eval,
        "execution_request_boundary": execution_request_boundary,
        "execution_idempotency": execution_idempotency,
        "execution_receipt": receipt,
        "execution_gateway": execution_gateway,
        "execution_pilot": execution_pilot,
        "approval_session": approval_session,
        "durable_approval_session": durable_approval_record,
        "idempotency_record": idempotency_record,
    }


async def _apply_diagnostics(
    *,
    resp: Any,
    req: AnswerRequest,
    http: Request,
    workspace_id: str,
    retriever: object,
    llm: object | None,
    llm_enabled: bool,
    llm_provider_name: str,
    llm_model: str,
    llm_error: str,
    assistant_mode_enabled: bool,
    assistant_proactive_enabled: bool,
    assistant_actions_enabled: bool,
    assistant_response_language: str,
    session_memory_loaded: bool,
    session_memory_hit: bool,
    durable_approval_record_loaded: bool,
    durable_idempotency_record_loaded: bool,
) -> None:
    try:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        diag.setdefault("retrieved_provenance_count", int(len(getattr(resp, "provenance", []) or [])))
        diag.setdefault("used_chunks_count", int(len(getattr(resp, "used_chunks", []) or [])))
        diag.setdefault("used_nodes_count", int(len(getattr(resp, "used_nodes", []) or [])))
        diag.setdefault("used_edges_count", int(len(getattr(resp, "used_edges", []) or [])))
        diag.setdefault("has_llm", bool(llm is not None))
        diag.setdefault("query_len", int(len(req.query or "")))
        diag.setdefault("k", int(req.k or 0))
        diag.setdefault("graph_depth", int(req.graph_depth or 0))
        diag.setdefault("session_id", str(getattr(req, "session_id", "") or ""))
        diag.setdefault("evidence_contract_version", EVIDENCE_CONTRACT_VERSION)
        contract = dict(diag.get("evidence_contract") or {})
        diag.setdefault(
            "evidence_contract_valid_minimal",
            bool(contract.get("valid_minimal", False)),
        )
        diag.setdefault(
            "evidence_contract_missing_minimal_fields",
            list(contract.get("missing_minimal_fields") or []),
        )
        diag.setdefault(
            "evidence_contract_missing_minimal_count",
            int(contract.get("missing_minimal_count") or len(contract.get("missing_minimal_fields") or [])),
        )
        diag.setdefault(
            "evidence_contract_minimal_coverage_score",
            float(contract.get("minimal_coverage_score") or 0.0),
        )
        if bool(diag.get("evidence_contract_valid_minimal", False)):
            diag.setdefault("evidence_contract_gate_reason", "ok")
        else:
            missing = list(diag.get("evidence_contract_missing_minimal_fields") or [])
            if missing:
                diag.setdefault("evidence_contract_gate_reason", "missing:" + ",".join(str(x) for x in missing))
            else:
                diag.setdefault("evidence_contract_gate_reason", "invalid")
        diag.setdefault(
            "self_check",
            {
                "version": "v1",
                "status": (
                    "pass"
                    if (
                        float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                        >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                        and int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                        <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                    )
                    else "warn"
                ),
                "reasons": (
                    []
                    if (
                        float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                        >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                        and int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                        <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                    )
                    else [
                        *(
                            [
                                f"threshold:minimal_coverage_score<{float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN):.1f}"
                            ]
                            if float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                            < float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                            else []
                        ),
                        *(
                            [
                                f"threshold:missing_minimal_count>{int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)}"
                            ]
                            if int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                            > int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                            else []
                        ),
                    ]
                ),
                "policy_mode": "warning_only",
                "inputs": {
                    "evidence_contract_valid_minimal": bool(
                        diag.get("evidence_contract_valid_minimal", False)
                    ),
                    "evidence_contract_missing_minimal_count": int(
                        diag.get("evidence_contract_missing_minimal_count", 0) or 0
                    ),
                    "evidence_contract_minimal_coverage_score": float(
                        diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0
                    ),
                },
                "thresholds": {
                    "minimal_coverage_score_min": float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN),
                    "missing_minimal_count_max": int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX),
                },
            },
        )
        self_check = dict(diag.get("self_check") or {})
        if str(self_check.get("status", "")) == "warn":
            resp.warnings = list(getattr(resp, "warnings", []) or [])
            if "self_check_warning" not in resp.warnings:
                resp.warnings.append("self_check_warning")
        diag.setdefault(
            "verify",
            {
                "version": VERIFY_DIAGNOSTICS_VERSION,
                "status": (
                    "pass"
                    if (
                        str(self_check.get("status", "") or "")
                        == str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                        and str(self_check.get("policy_mode", "") or "")
                        == str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                        and int(len(self_check.get("reasons") or []))
                        <= int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                    )
                    else "warn"
                ),
                "reasons": (
                    []
                    if (
                        str(self_check.get("status", "") or "")
                        == str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                        and str(self_check.get("policy_mode", "") or "")
                        == str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                        and int(len(self_check.get("reasons") or []))
                        <= int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                    )
                    else [
                        *(
                            [f"self_check_status!={VERIFY_SELF_CHECK_STATUS_REQUIRED}"]
                            if str(self_check.get("status", "") or "")
                            != str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                            else []
                        ),
                        *(
                            [f"self_check_policy_mode!={VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED}"]
                            if str(self_check.get("policy_mode", "") or "")
                            != str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                            else []
                        ),
                        *(
                            [f"self_check_reasons_count>{int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)}"]
                            if int(len(self_check.get("reasons") or []))
                            > int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                            else []
                        ),
                    ]
                ),
                "policy_mode": "warning_only",
                "inputs": {
                    "planner_path_used": bool(diag.get("planner_path_used", False)),
                    "self_check_status": str(self_check.get("status", "") or ""),
                    "self_check_policy_mode": str(self_check.get("policy_mode", "") or ""),
                    "self_check_reasons_count": int(len(self_check.get("reasons") or [])),
                },
                "thresholds": {
                    "required_self_check_status": str(VERIFY_SELF_CHECK_STATUS_REQUIRED),
                    "required_self_check_policy_mode": str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED),
                    "self_check_reasons_count_max": int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX),
                },
            },
        )
        verify = dict(diag.get("verify") or {})
        if str(verify.get("status", "")) == "warn":
            resp.warnings = list(getattr(resp, "warnings", []) or [])
            if "verify_warning" not in resp.warnings:
                resp.warnings.append("verify_warning")
        coverage_score = float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
        missing_claims = int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
        raw_conf = max(0.0, min(1.0, coverage_score - float(missing_claims * 0.15)))
        policy = build_reasoning_execution_policy()
        max_retries = int(policy.get("max_retries", 0) or 0)
        retry_budget_available = bool(raw_conf < 0.6 and max_retries > 0)
        diag.setdefault("reasoning_execution_policy", dict(policy))
        diag.setdefault(
            "reasoning_quality",
            {
                "version": "v1",
                "claims_total": 0,
                "claims_sample": [],
                "coverage": {
                    "claims_total": 0,
                    "claims_covered": 0,
                    "claims_uncovered": 0,
                    "coverage_score": coverage_score,
                    "covered_claim_indices": [],
                    "uncovered_claim_indices": [],
                },
                "confidence": {
                    "coverage_score": coverage_score,
                    "unsupported_claims": 0,
                    "missing_claims": missing_claims,
                    "penalty_unsupported": 0.0,
                    "penalty_missing": float(missing_claims * 0.15),
                    "penalty_total": float(missing_claims * 0.15),
                    "raw_confidence": raw_conf,
                    "confidence_score": raw_conf,
                },
                "retry": {
                    "attempt": 0,
                    "max_retries": max_retries,
                    "confidence_score": raw_conf,
                    "threshold": 0.6,
                    "confidence_below_threshold": bool(raw_conf < 0.6),
                    "retry_budget_available": bool(retry_budget_available),
                    "should_retry": bool(retry_budget_available),
                    "next_attempt": 1 if retry_budget_available else 0,
                    "loop_guard_triggered": False,
                    "reason": (
                        "retry_allowed_low_confidence"
                        if retry_budget_available
                        else "retry_not_needed_confidence_ok"
                    ),
                },
            },
        )
        reasoning_quality = dict(diag.get("reasoning_quality") or {})
        diag.setdefault(
            "reasoning_benchmark",
            {
                "suite_name": "reasoning_runtime_fallback",
                "summary": {
                    "suite_name": "reasoning_runtime_fallback",
                    "total_cases": 0,
                    "passed_cases": 0,
                    "pass_rate": 0.0,
                    "average_score": 0.0,
                    "results": [],
                },
                "failed_case_ids": [],
                "average_latency_ms": 0,
                "results": [],
            },
        )
        diag.setdefault(
            "reasoning_optimization",
            {
                "signal": {
                    "trace_id": str(diag.get("trace_id", "") or ""),
                    "confidence_score": 0.0,
                    "coverage_score": 0.0,
                    "pass_rate": 0.0,
                    "average_latency_ms": 0,
                    "warnings_count": int(len(list(getattr(resp, "warnings", []) or []))),
                    "retry_rate": 0.0,
                    "signal_tags": [],
                },
                "proposals": [],
                "decision": {
                    "decision_id": "optimization_decision:runtime",
                    "action": "defer",
                    "selected_proposal_ids": [],
                    "reason_codes": ["no_proposals"],
                    "confidence": 0.0,
                    "requires_human_review": False,
                },
            },
        )
        diag.setdefault(
            "enterprise_productization",
            {
                "release_gate_policy": {
                    "profile_name": "enterprise_default",
                    "required_checks": [],
                    "blocking_checks": [],
                    "minimum_pass_rate": 0.8,
                    "minimum_average_score": 0.7,
                    "minimum_coverage_ratio": 0.0,
                    "allow_skipped": False,
                    "require_benchmark_summary": True,
                    "require_optimization_review": True,
                    "allowed_warning_codes": [],
                },
                "release_checks": {},
                "readiness": {
                    "profile_name": "enterprise_default",
                    "release_gate_passed": False,
                    "failed_checks": [],
                    "benchmark_pass_rate": 0.0,
                    "benchmark_average_score": 0.0,
                    "optimization_action": "defer",
                    "optimization_requires_review": False,
                    "warnings_count": int(len(list(getattr(resp, "warnings", []) or []))),
                    "readiness_score": 0.0,
                    "reason_codes": [],
                },
                "rollout_decision": {
                    "decision_id": "enterprise_rollout:runtime",
                    "action": "defer",
                    "target_environment": "production",
                    "blocked_by": [],
                    "reason_codes": ["no_runtime_enterprise_inputs"],
                    "confidence": 0.0,
                    "requires_human_approval": True,
                },
            },
        )
        diag.setdefault(
            "meta_cognition",
            {
                "uncertainty": {
                    "status": "low",
                    "uncertainty_score": 0.0,
                    "signals": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
                "gap_map": {
                    "session_id": str(diag.get("session_id", "") or ""),
                    "status": "clear",
                    "total_gaps": 0,
                    "high_priority_gaps": 0,
                    "coverage_score": 1.0,
                    "gaps": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
                "reflection": {
                    "status": "ready",
                    "confidence_score": 1.0,
                    "uncertainty_score": 0.0,
                    "coverage_score": 1.0,
                    "insight_count": 0,
                    "insights": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
            },
        )
        diag.setdefault(
            "reasoning_trace",
            {
                "query": str(getattr(req, "query", "") or ""),
                "plan": [],
                "steps": [],
                "verify_results": [],
                "quality": reasoning_quality,
                "timeline": {"events": [], "total_duration_ms": 0},
                "answer": str(getattr(resp, "answer", "") or ""),
            },
        )
        diag.setdefault(
            "anticipatory",
            {
                "whisper_receipt": {
                    "run_id": "whisper:pending",
                    "status": "skipped",
                    "safe_mode": True,
                    "duration_ms": 0,
                    "suggestion_count": 0,
                    "reason_codes": ["anticipatory_not_run"],
                    "warnings": [],
                },
                "opportunity_scan": {
                    "status": "idle",
                    "opportunity_score": 0.0,
                    "signals": [],
                    "reason_codes": [],
                    "warnings": [],
                },
                "proactive_suggestions": {
                    "status": "idle",
                    "suggestions": [],
                    "top_suggestion_id": "",
                    "reason_codes": [],
                    "warnings": [],
                },
                "draft_actions": {
                    "status": "idle",
                    "actions": [],
                    "top_action_id": "",
                    "requires_confirmation": False,
                    "reason_codes": [],
                    "warnings": [],
                },
            },
        )
        trace = dict(diag.get("reasoning_trace") or {})
        diag.setdefault(
            "reasoning_timeline",
            dict(trace.get("timeline") or {"events": [], "total_duration_ms": 0}),
        )
        diag.setdefault("session_memory_loaded", bool(session_memory_loaded))
        diag.setdefault("session_memory_hit", bool(session_memory_hit))
        memory_consistency = _build_memory_consistency_bundle(
            session_memory_loaded=bool(session_memory_loaded),
            session_memory_hit=bool(session_memory_hit),
            durable_approval_record_loaded=bool(durable_approval_record_loaded),
            durable_idempotency_record_loaded=bool(durable_idempotency_record_loaded),
        )
        memory_consistency_strategy = _build_memory_consistency_strategy_contract()
        planner_runtime_parity = _build_planner_runtime_parity_fallback_bundle(diagnostics=diag)
        diag.setdefault("memory_consistency", memory_consistency)
        diag.setdefault("memory_consistency_strategy", memory_consistency_strategy)
        diag.setdefault("planner_runtime_parity", planner_runtime_parity)
        diag.setdefault("evidence_type_counts", {})
        # top_evidence: prefer retriever snapshot; fallback to response used_chunks
        try:
            tops = list(getattr(retriever, "last_top_evidence", []) or [])
        except Exception:
            tops = []
        if not tops:
            try:
                tops = [f"chunk:{x}" for x in (getattr(resp, "used_chunks", []) or [])[:10]]
            except Exception:
                tops = []
        if session_memory_hit:
            sid = str(getattr(req, "session_id", "") or "default")
            tops = [f"memory:session:{sid}:last_answer", *list(tops or [])]
            tops = tops[:10]
        diag.setdefault("top_evidence", tops)
        # trace_id must be present in diagnostics (debug snapshot expects it)
        rid = str(get_request_id(http) or "")
        try:
            from src.observability.trace import make_trace_id

            diag.setdefault(
                "trace_id",
                make_trace_id(
                    workspace_id=str(workspace_id or ""),
                    request_id=rid,
                ),
            )
        except Exception:
            # Fallback: stable correlation id even without tracing deps
            diag.setdefault("trace_id", rid or "")

        # LLM diagnostics
        diag.setdefault("llm_enabled", bool(llm_enabled))
        diag.setdefault("llm_provider", llm_provider_name)
        diag.setdefault("llm_model", llm_model)
        diag.setdefault("llm_error", llm_error)
        diag.setdefault("assistant_contract_version", "v1")
        diag.setdefault("intent_contract_version", INTENT_CONTRACT_VERSION)
        diag.setdefault(
            "response_mode",
            (
                "strict_rag"
                if int(diag.get("retrieved_provenance_count", 0) or 0) > 0
                else "assistant_fallback"
            ),
        )
        diag.setdefault("response_language", str(assistant_response_language or "auto"))
        diag.setdefault("assistant_mode_enabled", bool(assistant_mode_enabled))
        diag.setdefault("assistant_proactive_enabled", bool(assistant_proactive_enabled))
        diag.setdefault("assistant_actions_enabled", bool(assistant_actions_enabled))
        intent = _infer_assistant_intent(
            query=str(getattr(req, "query", "") or ""),
            assistant_mode_enabled=assistant_mode_enabled,
        )
        diag.setdefault(
            "assistant_intent",
            {
                "intent": str(intent.get("intent", "general_query") or "general_query"),
                "confidence": float(intent.get("confidence", 0.0) or 0.0),
                "entities": dict(intent.get("entities") or {}),
                "implicit_tasks": list(intent.get("implicit_tasks") or []),
                "source": str(intent.get("source", "heuristic") or "heuristic"),
            },
        )
        intent, plan, llm_planner = await _build_planner_with_fallback(
            query=str(getattr(req, "query", "") or ""),
            intent_payload=intent,
            assistant_mode_enabled=assistant_mode_enabled,
            llm=llm,
            llm_enabled=bool(llm_enabled),
            llm_model=str(llm_model or ""),
            llm_error=str(llm_error or ""),
        )
        llm_planner_policy = _build_llm_planner_policy_contract(
            allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
        )
        intent, plan, llm_planner, llm_planner_policy_eval = _apply_llm_planner_policy_guards(
            intent_payload=intent,
            plan_bundle=plan,
            llm_planner_bundle=llm_planner,
            policy_contract=llm_planner_policy,
            query=str(getattr(req, "query", "") or ""),
            assistant_mode_enabled=assistant_mode_enabled,
            deterministic_plan_builder=_build_deterministic_plan,
        )
        plan, planning_policy = _apply_plan_policy_guards(plan_bundle=plan, max_steps=5)
        mcp_tools = _load_mcp_tools_from_runtime(http)
        tool_selection = _build_tool_selection_bundle(
            plan_bundle=plan,
            assistant_mode_enabled=assistant_mode_enabled,
            mcp_tools=mcp_tools,
        )
        tool_selection_policy = _build_tool_selection_policy_contract()
        tool_selection, tool_selection_policy_eval = _apply_tool_selection_policy_guards(
            tool_selection_bundle=tool_selection,
            policy_contract=tool_selection_policy,
            plan_bundle=plan,
        )
        feedback_learning = _build_feedback_learning_bundle(
            req=req,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        feedback_policy = _build_feedback_policy_contract()
        feedback_learning, feedback_policy_eval = _apply_feedback_policy_guards(
            feedback_bundle=feedback_learning,
            policy_contract=feedback_policy,
        )
        feedback_adaptation = _build_feedback_adaptation_bundle(
            feedback_bundle=feedback_learning,
            intent_bundle=intent,
            plan_bundle=plan,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        adaptation_policy = _build_feedback_adaptation_policy_contract(
            allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
        )
        feedback_adaptation, adaptation_policy_eval = _apply_feedback_adaptation_policy_guards(
            adaptation_bundle=feedback_adaptation,
            policy_contract=adaptation_policy,
        )
        diag.setdefault("plan_contract_version", PLAN_CONTRACT_VERSION)
        diag.setdefault("assistant_plan", dict(plan))
        llm_planner["plan_id"] = str(plan.get("plan_id", "") or "")
        diag.setdefault("llm_planner_contract_version", LLM_PLANNER_CONTRACT_VERSION)
        diag.setdefault("assistant_llm_planner", llm_planner)
        diag.setdefault("tool_selection_contract_version", TOOL_SELECTION_CONTRACT_VERSION)
        diag.setdefault("assistant_tool_selection", tool_selection)
        diag.setdefault("tool_selection_policy", tool_selection_policy_eval)
        diag.setdefault("feedback_contract_version", FEEDBACK_CONTRACT_VERSION)
        diag.setdefault("assistant_feedback_learning", feedback_learning)
        diag.setdefault("feedback_policy", feedback_policy_eval)
        diag.setdefault("adaptation_contract_version", ADAPTATION_CONTRACT_VERSION)
        diag.setdefault("assistant_feedback_adaptation", feedback_adaptation)
        diag.setdefault("adaptation_policy", adaptation_policy_eval)
        diag.setdefault("llm_planner_policy", llm_planner_policy_eval)
        diag.setdefault("planning_policy", dict(planning_policy))
        diag = _wire_runtime_diagnostics(diagnostics=diag)
        execution_orchestration = _run_assistant_execution_orchestration_seam(
            req=req,
            diagnostics=diag,
            plan_bundle=plan,
            workspace_id=str(workspace_id or ""),
            request_id=str(get_request_id(http) or ""),
            assistant_mode_enabled=assistant_mode_enabled,
            assistant_actions_enabled=assistant_actions_enabled,
        )
        handshake = dict(execution_orchestration.get("handshake") or {})
        transition_policy_eval = dict(execution_orchestration.get("execution_transition_policy") or {})
        execution_request_boundary = dict(execution_orchestration.get("execution_request_boundary") or {})
        execution_idempotency = dict(execution_orchestration.get("execution_idempotency") or {})
        receipt = dict(execution_orchestration.get("execution_receipt") or {})
        execution_gateway = dict(execution_orchestration.get("execution_gateway") or {})
        execution_pilot = dict(execution_orchestration.get("execution_pilot") or {})
        approval_session = dict(execution_orchestration.get("approval_session") or {})
        durable_approval_record = dict(execution_orchestration.get("durable_approval_session") or {})
        idempotency_record = dict(execution_orchestration.get("idempotency_record") or {})
        diag.setdefault("execution_handshake_contract_version", HANDSHAKE_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_handshake", handshake)
        diag.setdefault("execution_transition_policy", transition_policy_eval)
        diag.setdefault("execution_request_boundary", execution_request_boundary)
        diag.setdefault("execution_idempotency", execution_idempotency)
        diag.setdefault("execution_receipt_contract_version", EXECUTION_RECEIPT_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_receipt", receipt)
        diag.setdefault("execution_gateway_contract_version", EXECUTION_GATEWAY_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_gateway", execution_gateway)
        diag.setdefault("execution_pilot_contract_version", EXECUTION_PILOT_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_pilot", execution_pilot)
        diag.setdefault("approval_session_contract_version", APPROVAL_SESSION_CONTRACT_VERSION)
        diag.setdefault("assistant_approval_session", approval_session)
        diag.setdefault("durable_approval_session_contract_version", DURABLE_APPROVAL_SESSION_CONTRACT_VERSION)
        diag.setdefault("assistant_durable_approval_session", durable_approval_record)
        diag.setdefault("idempotency_record_contract_version", IDEMPOTENCY_RECORD_CONTRACT_VERSION)
        diag.setdefault("assistant_idempotency_record", idempotency_record)
        governance_subcore = build_governance_subcore_bundle(
            reasoning_trace=dict(diag.get("reasoning_trace") or {}),
            reasoning_timeline=dict(diag.get("reasoning_timeline") or {}),
            execution_receipt=receipt,
        )
        diag.setdefault("governance_subcore", governance_subcore)
        reason_codes = list(intent.get("reason_codes") or []) + list(plan.get("reason_codes") or [])
        reason_codes.extend(list(llm_planner.get("reason_codes") or []))
        reason_codes.extend(list(tool_selection.get("reason_codes") or []))
        reason_codes.extend(list(tool_selection_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(feedback_learning.get("reason_codes") or []))
        reason_codes.extend(list(feedback_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(feedback_adaptation.get("reason_codes") or []))
        reason_codes.extend(list(adaptation_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(llm_planner_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(planning_policy.get("reason_codes") or []))
        reason_codes.extend(list(handshake.get("reason_codes") or []))
        reason_codes.extend(list(execution_idempotency.get("reason_codes") or []))
        reason_codes.extend(list(execution_request_boundary.get("reason_codes") or []))
        reason_codes.extend(list(receipt.get("reason_codes") or []))
        reason_codes.extend(list(execution_gateway.get("reason_codes") or []))
        reason_codes.extend(list(execution_pilot.get("reason_codes") or []))
        reason_codes.extend(list(approval_session.get("reason_codes") or []))
        reason_codes.extend(list(durable_approval_record.get("reason_codes") or []))
        reason_codes.extend(list(idempotency_record.get("reason_codes") or []))
        reason_codes.extend(list(governance_subcore.get("reason_codes") or []))
        reason_codes.extend(list(memory_consistency.get("reason_codes") or []))
        reason_codes.extend(list(memory_consistency_strategy.get("reason_codes") or []))
        reason_codes.extend(list(planner_runtime_parity.get("reason_codes") or []))
        reason_codes = sorted(set([str(x) for x in reason_codes if str(x or "").strip()]))
        diag.setdefault("planning_reason_codes", reason_codes)
        diag.setdefault("plan_id", str(plan.get("plan_id", "") or ""))

        # Memory evidence observability (A2.1)
        try:
            etc = dict(diag.get("evidence_type_counts") or {})
            if session_memory_hit:
                etc["memory"] = int(etc.get("memory", 0)) + 1
            diag["evidence_type_counts"] = etc
        except Exception as exc:
            diag = _append_planning_reason_codes(
                diagnostics=diag,
                reason_codes=["answer_service_evidence_type_counts_soft_failure"],
            )
            _LOGGER.warning(
                "Answer service soft-failure: evidence type counts diagnostics skipped",
                context={
                    "workspace_id": str(workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_evidence_type_counts_soft_failure",
                },
            )

        # Retriever stats (best-effort)
        try:
            diag.setdefault("retriever_stats", dict(getattr(retriever, "last_stats", {}) or {}))
        except Exception as exc:
            diag = _append_planning_reason_codes(
                diagnostics=diag,
                reason_codes=["answer_service_retriever_stats_soft_failure"],
            )
            _LOGGER.warning(
                "Answer service soft-failure: retriever stats diagnostics skipped",
                context={
                    "workspace_id": str(workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_retriever_stats_soft_failure",
                },
            )

        resp.diagnostics = diag
    except Exception as exc:
        fallback_diag = _append_planning_reason_codes(
            diagnostics=dict(getattr(resp, "diagnostics", None) or {}),
            reason_codes=["answer_service_apply_diagnostics_soft_failure"],
        )
        try:
            resp.diagnostics = fallback_diag
        except Exception:
            object.__setattr__(resp, "diagnostics", fallback_diag)
        _LOGGER.warning(
            "Answer service soft-failure: diagnostics assembly skipped",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_service_apply_diagnostics_soft_failure",
            },
        )


async def _load_session_memory(
    *,
    req: AnswerRequest,
    workspace_id: str,
    get_memory_store: object,
) -> tuple[bool, bool]:
    # A2.1 session memory (MVP): load latest turn per session, best-effort.
    try:
        sid = str(getattr(req, "session_id", "") or "default")
        mem = get_memory_store()
        prev = await mem.get(workspace_id=workspace_id, key=f"session:{sid}:last_answer")
        req.session_memory_last_answer = _clip_text(prev)
        session_memory_loaded = True
        session_memory_hit = bool(req.session_memory_last_answer)
    except Exception:
        req.session_memory_last_answer = ""
        session_memory_loaded = False
        session_memory_hit = False
    return session_memory_loaded, session_memory_hit


async def _save_session_memory(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> None:
    # A2.1 session memory (MVP): persist latest turn per session, best-effort.
    try:
        sid = str(getattr(req, "session_id", "") or "default")
        mem = get_memory_store()
        await mem.put(
            workspace_id=workspace_id,
            key=f"session:{sid}:last_answer",
            value=_clip_text(getattr(resp, "answer", "")),
            metadata={
                "session_id": sid,
                "query": str(getattr(req, "query", "") or ""),
            },
        )
        resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
        resp.diagnostics.setdefault("session_memory_saved", True)
    except Exception:
        try:
            resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
            resp.diagnostics.setdefault("session_memory_saved", False)
        except Exception as fallback_exc:
            _LOGGER.warning(
                "Answer service soft-failure: session memory failure diagnostics skipped",
                context={
                    "workspace_id": str(workspace_id or ""),
                    "error": str(fallback_exc),
                    "error_type": type(fallback_exc).__name__,
                    "reason_code": "answer_service_session_memory_failure_diagnostics_soft_failure",
                },
            )


class _AnticipatorySessionWriter:
    def __init__(self, *, workspace_id: str, session_id: str, get_memory_store: object) -> None:
        self._workspace_id = workspace_id
        self._session_id = session_id
        self._get_memory_store = get_memory_store
        self._buffer: dict[str, object] = {}

    def store(self, *, key: str, value: object) -> None:
        self._buffer[str(key)] = value

    async def flush(self) -> None:
        if not self._buffer:
            return
        mem = self._get_memory_store()
        for key, value in sorted(self._buffer.items(), key=lambda x: str(x[0])):
            await mem.put(
                workspace_id=self._workspace_id,
                key=f"session:{self._session_id}:{str(key)}",
                value=value,
                metadata={"session_id": self._session_id, "kind": str(key)},
            )


async def _run_anticipatory_safe_mode(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> dict[str, object]:
    sid = str(getattr(req, "session_id", "") or "default")
    writer = _AnticipatorySessionWriter(
        workspace_id=workspace_id,
        session_id=sid,
        get_memory_store=get_memory_store,
    )
    context = str(getattr(req, "query", "") or "")
    answer = str(getattr(resp, "answer", "") or "")
    merged_context = f"{context}\n{answer}".strip()
    runner = WhisperRunner(scanner=OpportunityScanner(), safe_mode=True)
    whisper = await runner.run_in_background(
        context=merged_context,
        session_memory=str(getattr(req, "session_memory_last_answer", "") or ""),
        registry=None,
        suggestion_limit=3,
        session_writer=writer,
    )
    await writer.flush()
    raw_suggestions = list(whisper.get("suggestions") or [])
    proactive_rows: list[dict[str, object]] = []
    for row in raw_suggestions:
        item = dict(row or {})
        proactive_rows.append(
            {
                "suggestion_id": str(item.get("suggestion_id", "") or ""),
                "suggestion_type": str(item.get("type", "follow_up") or "follow_up"),
                "confidence": float(item.get("confidence", 0.0) or 0.0),
                "rationale": str(item.get("reason", "") or ""),
                "action_hint": str(item.get("trigger", "") or ""),
                "source_signal_id": str(item.get("suggestion_id", "") or "").replace("suggestion:", ""),
            }
        )
    proactive_bundle = build_proactive_suggestion_bundle(suggestions=proactive_rows, limit=3, warnings=[])
    return {
        "whisper_receipt": dict(whisper.get("receipt") or {}),
        "opportunity_scan": dict(whisper.get("scan") or {}),
        "proactive_suggestions": dict(proactive_bundle),
    }


async def _build_llm_adapter(*, settings: object) -> tuple[object | None, bool, str, str, str]:
    llm_enabled = bool(getattr(settings, "feature_reasoning_llm_enabled", False))
    llm = None
    llm_provider_name = ""
    llm_model = ""
    llm_error = ""

    if llm_enabled:
        try:
            from src.api.dependencies_impl import get_llm_provider

            prov = await get_llm_provider()
            # Determine provider/model for diagnostics in a provider-aware way
            try:
                llm_provider_name = str(getattr(settings, "llm_provider").value)
            except Exception:
                llm_provider_name = str(getattr(settings, "llm_provider", "") or "")
            if llm_provider_name == "openai":
                llm_model = str(getattr(settings, "openai_model", "") or "")
            elif llm_provider_name == "ollama":
                llm_model = str(getattr(settings, "ollama_model", "") or "")
            else:
                llm_model = str(getattr(prov, "model", "") or "")
            llm = LLMGenerateAdapter(prov, provider_name=llm_provider_name, model=llm_model)
        except Exception as e:
            llm = None
            llm_error = str(e)

    return llm, llm_enabled, llm_provider_name, llm_model, llm_error


class RetrieverAdapter:
    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        self._engine = engine
        self._hybrid = hybrid
        self._workspace_id = workspace_id
        self.last_stats: dict[str, object] = {}
        self.last_top_evidence: list[str] = []

    async def retrieve(self, request: AnswerRequest):
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=0.0,
            graph_depth=request.graph_depth,
            evidence_max_total=int(getattr(request, "evidence_max_total", 50) or 50),
            evidence_max_chunks=getattr(request, "evidence_max_chunks", None),
            evidence_max_memory=getattr(request, "evidence_max_memory", None),
            evidence_max_edges=getattr(request, "evidence_max_edges", None),
            evidence_dedupe=bool(getattr(request, "evidence_dedupe", True)),
            evidence_rerank=bool(getattr(request, "evidence_rerank", True)),
        )

        graph = getattr(out, "graph", None)
        evidence = getattr(out, "evidence", None)
        results = getattr(out, "results", None)

        if isinstance(out, dict):
            graph = out.get("graph")
            evidence = out.get("evidence")
            results = out.get("results")

        graph = graph or {"nodes": [], "edges": []}
        evidence = list(evidence or [])
        results = list(results or [])

        # merge retriever stats (best-effort)
        try:
            stats = out.get("stats") if isinstance(out, dict) else getattr(out, "stats", None)
            if isinstance(stats, dict) and stats:
                self.last_stats = dict(self.last_stats or {})
                for k, v in stats.items():
                    self.last_stats.setdefault(str(k), v)
        except Exception as exc:
            _LOGGER.warning(
                "Answer service soft-failure: retriever adapter stats merge skipped",
                context={
                    "workspace_id": str(self.workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_retriever_adapter_stats_merge_soft_failure",
                },
            )

        # Hybrid retriever owns evidence policy in A1.5. Keep adapter diagnostics additive only.
        self.last_stats = dict(self.last_stats or {})
        try:
            self.last_stats.setdefault("vector_candidates_count", int(len(results or [])))
            self.last_stats.setdefault("graph_nodes_count", int(len((graph or {}).get("nodes") or [])))
            self.last_stats.setdefault("graph_edges_count", int(len((graph or {}).get("edges") or [])))
            self.last_stats.setdefault("evidence_after_policy_count", int(len(evidence or [])))
        except Exception as exc:
            _LOGGER.warning(
                "Answer service soft-failure: retriever adapter additive stats skipped",
                context={
                    "workspace_id": str(self.workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_retriever_adapter_additive_stats_soft_failure",
                },
            )


        # Build debug "top_evidence" list (best-effort). Test expects at least one "chunk:*" when evidence exists.
        try:
            tops: list[str] = []
            for item in (evidence or [])[:10]:
                if isinstance(item, dict):
                    cid = item.get("chunk_id") or item.get("id") or item.get("doc_id")
                    if cid:
                        tops.append(f"chunk:{cid}")
                else:
                    # If evidence is already a string/id-like, keep it as chunk reference
                    s = str(item)
                    if s:
                        tops.append(f"chunk:{s}")
            self.last_top_evidence = tops
        except Exception:
            self.last_top_evidence = []
        return {"results": results, "graph": graph, "evidence": evidence}


class LLMGenerateAdapter:
    """Adapt Base LLM provider (complete/messages) to ReasoningEngine contract (generate(prompt)->str)."""

    def __init__(self, provider: object, *, provider_name: str = "", model: str = ""):
        self._p = provider
        self.provider_name = provider_name
        self.model = model

    async def generate(self, prompt: str) -> str:
        from src.core.types import Message, MessageRole

        messages = [Message(role=MessageRole.USER, content=str(prompt or ""))]
        cfg: dict[str, Any] = {}
        if self.model:
            cfg["model"] = self.model

        if hasattr(self._p, "complete"):
            c = await self._p.complete(messages=messages, config=(cfg or None))
            text = getattr(c, "content", None)
            return str(text if text is not None else c)

        raise RuntimeError("LLM provider does not implement complete()")


class AnswerService:
    """Composition-friendly orchestration for /answer endpoint.

    Keeps FastAPI endpoint thin and concentrates gating/wiring/diagnostics here.
    """

    async def handle(
        self,
        http: Request,
        req,
        *,
        workspace_id: str,
        engine: object | None = None,
        retriever: object | None = None,
    ):
        contract = build_answer_service_request_contract(
            http=http,
            req=req,
            workspace_id=workspace_id,
            engine=engine,
            retriever=retriever,
        )
        return await self.handle_contract(contract)

    async def handle_contract(self, contract: AnswerServiceRequestContract):
        from src.core.config import get_settings
        from src.core.providers import get_reasoning_engine, get_memory_store

        http = contract.http
        req = contract.req
        workspace_id = str(contract.workspace_id or "")
        engine = contract.engine
        retriever = contract.retriever
        s = get_settings()
        runtime_context = _build_answer_service_runtime_context(settings=s)
        if not bool(runtime_context.get("reasoning_enabled", False)) or not bool(runtime_context.get("graphrag_enabled", False)):
            # Endpoint uses 404 for feature-gated routes
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        log_observability(http, workspace_id=workspace_id, req=req)

        engine = engine or getattr(http.app.state, "rag_engine", None)
        hybrid = retriever or getattr(http.app.state, "hybrid_retriever", None)
        if engine is None or hybrid is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Reasoning stack not initialized")

        pipeline = await _run_answer_primary_pipeline(
            http=http,
            req=req,
            workspace_id=workspace_id,
            settings=s,
            runtime_context=runtime_context,
            engine=engine,
            hybrid=hybrid,
            get_reasoning_engine=get_reasoning_engine,
            get_memory_store=get_memory_store,
        )
        resp = await run_answer_post_orchestration_flow(
            req=req,
            http=http,
            resp=pipeline.resp,
            workspace_id=workspace_id,
            assistant_mode_enabled=pipeline.assistant_mode_enabled,
            assistant_proactive_enabled=pipeline.assistant_proactive_enabled,
            assistant_actions_enabled=pipeline.assistant_actions_enabled,
            assistant_response_language=pipeline.assistant_response_language,
            loaded_durable_approval=pipeline.loaded_durable_approval,
            loaded_durable_idempotency=pipeline.loaded_durable_idempotency,
            get_memory_store=get_memory_store,
            deps=_build_post_orchestration_deps(),
        )

        resp = await run_answer_diagnostics_merge_flow(
            req=req,
            resp=resp,
            workspace_id=workspace_id,
            loaded_durable_approval=pipeline.loaded_durable_approval,
            loaded_durable_idempotency=pipeline.loaded_durable_idempotency,
            get_memory_store=get_memory_store,
            deps=_build_diagnostics_merge_deps(),
        )

        return resp
