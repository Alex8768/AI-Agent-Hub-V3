from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import Request

from src.adapters.logging_adapter import get_logger
from src.layers.pro.anticipatory import (
    run_answer_anticipatory_safe_mode as _run_answer_anticipatory_safe_mode_impl,
)
from src.layers.pro.reasoning.execution_plane.request_boundary import (
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
    run_assistant_execution_orchestration_seam as _run_assistant_execution_orchestration_seam_impl,
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
    build_feedback_adaptation_bundle as _build_feedback_adaptation_bundle_impl,
    build_feedback_learning_bundle as _build_feedback_learning_bundle_impl,
    build_feedback_policy_contract as _build_feedback_policy_contract,
    infer_assistant_intent as _infer_assistant_intent_impl,
    bridge_plan_to_draft_actions as _bridge_plan_to_draft_actions_impl,
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



def _execution_runtime_helpers():
    import importlib

    return importlib.import_module("src.services.answer.execution.runtime_helpers")


def _build_transition_policy_contract() -> dict[str, object]:
    return _execution_runtime_helpers().build_transition_policy_contract()


def _apply_handshake_transition_policy(
    *,
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    return _execution_runtime_helpers().apply_handshake_transition_policy(
        transition_input=transition_input,
        draft_actions_bundle=draft_actions_bundle,
        policy_contract=policy_contract,
    )


def _build_post_orchestration_deps() -> AnswerPostOrchestrationDeps:
    execution = _execution_runtime_helpers()
    return AnswerPostOrchestrationDeps(
        run_anticipatory_safe_mode=_run_anticipatory_safe_mode,
        rank_proactive_bundle=_rank_proactive_bundle,
        build_draft_action_bundle=_build_draft_action_bundle,
        wire_runtime_diagnostics=_wire_runtime_diagnostics,
        bridge_plan_to_draft_actions=_bridge_plan_to_draft_actions,
        build_execution_handshake_bundle=execution.build_execution_handshake_bundle,
        build_transition_policy_contract=execution.build_transition_policy_contract,
        apply_handshake_transition_policy=execution.apply_handshake_transition_policy,
        extract_handshake_transition_input=execution.extract_handshake_transition_input,
        apply_durable_confirmation_token_guards=execution.apply_durable_confirmation_token_guards,
        apply_execution_idempotency_guard=execution.apply_execution_idempotency_guard,
        apply_handshake_transition=execution.apply_handshake_transition,
        apply_rollback_contract_guard=execution.apply_rollback_contract_guard,
        run_execution_pilot_runtime=execution.run_execution_pilot_runtime,
        build_execution_receipt_stub=execution.build_execution_receipt_stub,
        build_safe_mode_execution_gateway=execution.build_safe_mode_execution_gateway,
        build_execution_pilot_bundle=execution.build_execution_pilot_bundle,
        build_approval_session_bundle=execution.build_approval_session_bundle,
        build_durable_approval_session_record=execution.build_durable_approval_session_record,
        build_idempotency_record_snapshot=execution.build_idempotency_record_snapshot,
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
    import importlib

    retriever_adapter_cls = getattr(
        importlib.import_module("src.services.answer.retrieval.runtime_retriever_adapter"),
        "RuntimeRetrieverAdapter",
    )

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
        retriever_adapter_cls=retriever_adapter_cls,
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


def _planner_runtime_helpers():
    import importlib

    return importlib.import_module("src.services.answer.planner.runtime_helpers")


def _rank_proactive_bundle(bundle: dict[str, object]) -> dict[str, object]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.response.proactive_ranking"),
        "rank_proactive_bundle",
    )
    return impl(bundle=bundle)


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
    return _planner_runtime_helpers().infer_assistant_intent(
        query=query,
        assistant_mode_enabled=assistant_mode_enabled,
    )


def _build_deterministic_plan(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    return _planner_runtime_helpers().build_deterministic_plan(
        query=query,
        intent_payload=intent_payload,
        assistant_mode_enabled=assistant_mode_enabled,
    )


def _parse_llm_planner_intent(raw_text: str) -> str:
    return _planner_runtime_helpers().parse_llm_planner_intent(raw_text)


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
    return await _planner_runtime_helpers().build_planner_with_fallback(
        query=query,
        intent_payload=intent_payload,
        assistant_mode_enabled=assistant_mode_enabled,
        llm=llm,
        llm_enabled=llm_enabled,
        llm_model=llm_model,
        llm_error=llm_error,
        deterministic_plan_builder=_build_deterministic_plan,
        parse_intent_fn=_parse_llm_planner_intent,
    )


def _build_conversational_runtime_parity_bundle(
    *,
    diagnostics: dict[str, object],
    query: str,
    answer: str,
) -> dict[str, object]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.response.conversational_runtime_parity"),
        "build_conversational_runtime_parity_bundle",
    )
    return impl(
        diagnostics=diagnostics,
        query=query,
        answer=answer,
        normalize_language_tag_fn=_normalize_language_tag,
        answer_language_fn=_answer_language,
        is_unknown_style_answer_fn=_is_unknown_style_answer,
    )


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
    return _build_feedback_adaptation_bundle_impl(
        feedback_bundle=feedback_bundle,
        intent_bundle=intent_bundle,
        plan_bundle=plan_bundle,
        assistant_mode_enabled=assistant_mode_enabled,
        adaptation_contract_version=ADAPTATION_CONTRACT_VERSION,
        allowed_intents=_LLM_PLANNER_ALLOWED_INTENTS,
    )


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
    return _bridge_plan_to_draft_actions_impl(
        plan_bundle=plan_bundle,
        draft_actions_bundle=draft_actions_bundle,
        language=language,
        actions_enabled=actions_enabled,
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
    execution = _execution_runtime_helpers()
    return _run_assistant_execution_orchestration_seam_impl(
        req=req,
        diagnostics=diagnostics,
        plan_bundle=plan_bundle,
        workspace_id=workspace_id,
        request_id=request_id,
        assistant_mode_enabled=assistant_mode_enabled,
        assistant_actions_enabled=assistant_actions_enabled,
        build_handshake_fn=execution.build_execution_handshake_bundle,
        build_transition_policy_fn=execution.build_transition_policy_contract,
        apply_handshake_transition_policy_fn=execution.apply_handshake_transition_policy,
        extract_handshake_transition_input_fn=execution.extract_handshake_transition_input,
        apply_execution_idempotency_guard_fn=execution.apply_execution_idempotency_guard,
        apply_handshake_transition_fn=execution.apply_handshake_transition,
        apply_rollback_contract_guard_fn=execution.apply_rollback_contract_guard,
        run_execution_pilot_runtime_fn=execution.run_execution_pilot_runtime,
        build_execution_receipt_stub_fn=execution.build_execution_receipt_stub,
        build_safe_mode_execution_gateway_fn=execution.build_safe_mode_execution_gateway,
        build_execution_pilot_bundle_fn=execution.build_execution_pilot_bundle,
        build_approval_session_bundle_fn=execution.build_approval_session_bundle,
        build_durable_approval_session_record_fn=execution.build_durable_approval_session_record,
        build_idempotency_record_snapshot_fn=execution.build_idempotency_record_snapshot,
    )


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
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.diagnostics.runtime_apply"),
        "apply_answer_diagnostics",
    )
    await impl(
        resp=resp,
        req=req,
        http=http,
        workspace_id=workspace_id,
        retriever=retriever,
        llm=llm,
        llm_enabled=llm_enabled,
        llm_provider_name=llm_provider_name,
        llm_model=llm_model,
        llm_error=llm_error,
        assistant_mode_enabled=assistant_mode_enabled,
        assistant_proactive_enabled=assistant_proactive_enabled,
        assistant_actions_enabled=assistant_actions_enabled,
        assistant_response_language=assistant_response_language,
        session_memory_loaded=session_memory_loaded,
        session_memory_hit=session_memory_hit,
        durable_approval_record_loaded=durable_approval_record_loaded,
        durable_idempotency_record_loaded=durable_idempotency_record_loaded,
        _build_planner_runtime_parity_fallback_bundle=_build_planner_runtime_parity_fallback_bundle,
        _infer_assistant_intent=_infer_assistant_intent,
        _build_planner_with_fallback=_build_planner_with_fallback,
        _load_mcp_tools_from_runtime=_load_mcp_tools_from_runtime,
        _build_tool_selection_bundle=_build_tool_selection_bundle,
        _build_feedback_learning_bundle=_build_feedback_learning_bundle,
        _build_feedback_adaptation_bundle=_build_feedback_adaptation_bundle,
        _run_assistant_execution_orchestration_seam=_run_assistant_execution_orchestration_seam,
        _append_planning_reason_codes=_append_planning_reason_codes,
        _wire_runtime_diagnostics=_wire_runtime_diagnostics,
        _build_memory_consistency_bundle=_build_memory_consistency_bundle,
        _build_memory_consistency_strategy_contract=_build_memory_consistency_strategy_contract,
        _build_deterministic_plan=_build_deterministic_plan,
        _LLM_PLANNER_ALLOWED_INTENTS=_LLM_PLANNER_ALLOWED_INTENTS,
        EXECUTION_GATEWAY_CONTRACT_VERSION=EXECUTION_GATEWAY_CONTRACT_VERSION,
        _LOGGER=_LOGGER,
    )


async def _load_session_memory(
    *,
    req: AnswerRequest,
    workspace_id: str,
    get_memory_store: object,
) -> tuple[bool, bool]:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.context.session_memory_runtime"),
        "load_session_memory",
    )
    return await impl(
        req=req,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )


async def _save_session_memory(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> None:
    import importlib

    impl = getattr(
        importlib.import_module("src.services.answer.context.session_memory_runtime"),
        "save_session_memory",
    )
    await impl(
        req=req,
        resp=resp,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
        logger=_LOGGER,
    )


async def _run_anticipatory_safe_mode(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> dict[str, object]:
    return await _run_answer_anticipatory_safe_mode_impl(
        req=req,
        resp=resp,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )


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
            import importlib

            llm_adapter_cls = getattr(
                importlib.import_module("src.services.answer.reasoning.llm_generate_adapter"),
                "LLMGenerateAdapter",
            )
            llm = llm_adapter_cls(
                prov,
                provider_name=llm_provider_name,
                model=llm_model,
            )
        except Exception as e:
            llm = None
            llm_error = str(e)

    return llm, llm_enabled, llm_provider_name, llm_model, llm_error


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
