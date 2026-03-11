from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AnswerPostOrchestrationDeps:
    run_anticipatory_safe_mode: object
    rank_proactive_bundle: object
    build_draft_action_bundle: object
    wire_runtime_diagnostics: object
    bridge_plan_to_draft_actions: object
    build_execution_handshake_bundle: object
    build_transition_policy_contract: object
    apply_handshake_transition_policy: object
    extract_handshake_transition_input: object
    apply_durable_confirmation_token_guards: object
    apply_execution_idempotency_guard: object
    apply_handshake_transition: object
    apply_rollback_contract_guard: object
    run_execution_pilot_runtime: object
    build_execution_receipt_stub: object
    build_safe_mode_execution_gateway: object
    build_execution_pilot_bundle: object
    build_approval_session_bundle: object
    build_durable_approval_session_record: object
    build_idempotency_record_snapshot: object
    append_planning_reason_codes: object
    get_request_id: object
    logger: object
    durable_approval_session_contract_version: str
    idempotency_record_contract_version: str
    execution_gateway_contract_version: str
    execution_pilot_contract_version: str


async def run_answer_post_orchestration_flow(
    *,
    req: object,
    http: object,
    resp: object,
    workspace_id: str,
    assistant_mode_enabled: bool,
    assistant_proactive_enabled: bool,
    assistant_actions_enabled: bool,
    assistant_response_language: str,
    loaded_durable_approval: dict[str, object],
    loaded_durable_idempotency: dict[str, object],
    get_memory_store: object,
    deps: AnswerPostOrchestrationDeps,
) -> object:
    try:
        if assistant_proactive_enabled:
            anticipatory = await deps.run_anticipatory_safe_mode(
                req=req,
                resp=resp,
                workspace_id=workspace_id,
                get_memory_store=get_memory_store,
            )
            anticipatory = dict(anticipatory or {})
            anticipatory["proactive_suggestions"] = deps.rank_proactive_bundle(
                dict(anticipatory.get("proactive_suggestions") or {})
            )
            anticipatory["draft_actions"] = deps.build_draft_action_bundle(
                proactive_bundle=dict(anticipatory.get("proactive_suggestions") or {}),
                language=str(assistant_response_language or "auto"),
                actions_enabled=assistant_actions_enabled,
            )
            diag = dict(getattr(resp, "diagnostics", None) or {})
            diag = deps.wire_runtime_diagnostics(diagnostics=diag)
            anticipatory["draft_actions"] = deps.bridge_plan_to_draft_actions(
                plan_bundle=dict(diag.get("assistant_plan") or {}),
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                language=str(assistant_response_language or "auto"),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
            resp.diagnostics["anticipatory"] = anticipatory
            resp.diagnostics = deps.wire_runtime_diagnostics(diagnostics=resp.diagnostics)
            plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
            handshake = deps.build_execution_handshake_bundle(
                plan_bundle=plan_bundle,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                assistant_mode_enabled=assistant_mode_enabled,
                actions_enabled=assistant_actions_enabled,
            )
            transition_policy = deps.build_transition_policy_contract()
            transition_input, transition_policy_eval = deps.apply_handshake_transition_policy(
                transition_input=deps.extract_handshake_transition_input(req),
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                policy_contract=transition_policy,
            )
            transition_input, token_guard_reasons = deps.apply_durable_confirmation_token_guards(
                transition_input=transition_input,
                durable_approval_record=loaded_durable_approval,
            )
            transition_policy_eval["applied_reason_codes"] = sorted(
                set(
                    [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                    + list(token_guard_reasons or [])
                )
            )
            transition_input, execution_idempotency = deps.apply_execution_idempotency_guard(
                transition_input=transition_input,
                workspace_id=str(workspace_id or ""),
                plan_id=str(plan_bundle.get("plan_id", "") or ""),
                prior_record=loaded_durable_idempotency,
            )
            handshake = deps.apply_handshake_transition(
                handshake_bundle=handshake,
                transition_input=transition_input,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
            )
            handshake, rollback_contract_eval = deps.apply_rollback_contract_guard(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
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
            resp.diagnostics["assistant_execution_handshake"] = handshake
            resp.diagnostics["execution_transition_policy"] = transition_policy_eval
            resp.diagnostics["execution_idempotency"] = execution_idempotency
            executed_action_ids, pilot_runtime_reasons = deps.run_execution_pilot_runtime(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["execution_transition_policy"]["applied_reason_codes"] = sorted(
                set(
                    [
                        str(x)
                        for x in list(
                            (dict(resp.diagnostics.get("execution_transition_policy") or {})).get(
                                "applied_reason_codes", []
                            )
                            or []
                        )
                        if str(x)
                    ]
                    + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
                )
            )
            resp.diagnostics["assistant_execution_receipt"] = deps.build_execution_receipt_stub(
                handshake_bundle=handshake,
                plan_bundle=plan_bundle,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                workspace_id=str(workspace_id or ""),
                request_id=str(deps.get_request_id(http) or ""),
                executed_action_ids=executed_action_ids,
            )
            resp.diagnostics["execution_gateway_contract_version"] = deps.execution_gateway_contract_version
            resp.diagnostics["assistant_execution_gateway"] = deps.build_safe_mode_execution_gateway(
                handshake_bundle=handshake,
                receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["execution_pilot_contract_version"] = deps.execution_pilot_contract_version
            resp.diagnostics["assistant_execution_pilot"] = deps.build_execution_pilot_bundle(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["assistant_approval_session"] = deps.build_approval_session_bundle(
                handshake_bundle=handshake,
                plan_bundle=plan_bundle,
                workspace_id=str(workspace_id or ""),
                request_id=str(deps.get_request_id(http) or ""),
            )
            resp.diagnostics["durable_approval_session_contract_version"] = deps.durable_approval_session_contract_version
            resp.diagnostics["assistant_durable_approval_session"] = deps.build_durable_approval_session_record(
                approval_session_bundle=dict(resp.diagnostics.get("assistant_approval_session") or {}),
                session_id=str(getattr(req, "session_id", "") or "default"),
                confirmation_token=str(handshake.get("confirmation_token", "") or ""),
                transition_input=transition_input,
                previous_record=loaded_durable_approval,
            )
            resp.diagnostics["idempotency_record_contract_version"] = deps.idempotency_record_contract_version
            resp.diagnostics["assistant_idempotency_record"] = deps.build_idempotency_record_snapshot(
                execution_idempotency_bundle=execution_idempotency,
                workspace_id=str(workspace_id or ""),
                plan_id=str(plan_bundle.get("plan_id", "") or ""),
                transition_input=transition_input,
            )
        else:
            resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
            base = dict(resp.diagnostics.get("anticipatory") or {})
            proactive = dict(base.get("proactive_suggestions") or {})
            reason_codes = sorted(
                set(
                    [
                        str(x)
                        for x in list(proactive.get("reason_codes") or [])
                        if str(x or "").strip()
                    ]
                    + ["assistant_proactive_disabled"]
                )
            )
            proactive["reason_codes"] = reason_codes
            base["proactive_suggestions"] = proactive
            base["draft_actions"] = deps.build_draft_action_bundle(
                proactive_bundle=proactive,
                language=str(assistant_response_language or "auto"),
                actions_enabled=False,
            )
            diag = dict(resp.diagnostics or {})
            diag = deps.wire_runtime_diagnostics(diagnostics=diag)
            base["draft_actions"] = deps.bridge_plan_to_draft_actions(
                plan_bundle=dict(diag.get("assistant_plan") or {}),
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                language=str(assistant_response_language or "auto"),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["anticipatory"] = base
            resp.diagnostics = deps.wire_runtime_diagnostics(diagnostics=resp.diagnostics)
            plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
            handshake = deps.build_execution_handshake_bundle(
                plan_bundle=plan_bundle,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                assistant_mode_enabled=assistant_mode_enabled,
                actions_enabled=assistant_actions_enabled,
            )
            transition_policy = deps.build_transition_policy_contract()
            transition_input, transition_policy_eval = deps.apply_handshake_transition_policy(
                transition_input=deps.extract_handshake_transition_input(req),
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                policy_contract=transition_policy,
            )
            transition_input, token_guard_reasons = deps.apply_durable_confirmation_token_guards(
                transition_input=transition_input,
                durable_approval_record=loaded_durable_approval,
            )
            transition_policy_eval["applied_reason_codes"] = sorted(
                set(
                    [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                    + list(token_guard_reasons or [])
                )
            )
            transition_input, execution_idempotency = deps.apply_execution_idempotency_guard(
                transition_input=transition_input,
                workspace_id=str(workspace_id or ""),
                plan_id=str(plan_bundle.get("plan_id", "") or ""),
                prior_record=loaded_durable_idempotency,
            )
            handshake = deps.apply_handshake_transition(
                handshake_bundle=handshake,
                transition_input=transition_input,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
            )
            handshake, rollback_contract_eval = deps.apply_rollback_contract_guard(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
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
            resp.diagnostics["assistant_execution_handshake"] = handshake
            resp.diagnostics["execution_transition_policy"] = transition_policy_eval
            resp.diagnostics["execution_idempotency"] = execution_idempotency
            executed_action_ids, pilot_runtime_reasons = deps.run_execution_pilot_runtime(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["execution_transition_policy"]["applied_reason_codes"] = sorted(
                set(
                    [
                        str(x)
                        for x in list(
                            (dict(resp.diagnostics.get("execution_transition_policy") or {})).get(
                                "applied_reason_codes", []
                            )
                            or []
                        )
                        if str(x)
                    ]
                    + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
                )
            )
            resp.diagnostics["assistant_execution_receipt"] = deps.build_execution_receipt_stub(
                handshake_bundle=handshake,
                plan_bundle=plan_bundle,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                workspace_id=str(workspace_id or ""),
                request_id=str(deps.get_request_id(http) or ""),
                executed_action_ids=executed_action_ids,
            )
            resp.diagnostics["execution_gateway_contract_version"] = deps.execution_gateway_contract_version
            resp.diagnostics["assistant_execution_gateway"] = deps.build_safe_mode_execution_gateway(
                handshake_bundle=handshake,
                receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["execution_pilot_contract_version"] = deps.execution_pilot_contract_version
            resp.diagnostics["assistant_execution_pilot"] = deps.build_execution_pilot_bundle(
                handshake_bundle=handshake,
                draft_actions_bundle=dict(base.get("draft_actions") or {}),
                receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                actions_enabled=assistant_actions_enabled,
            )
            resp.diagnostics["assistant_approval_session"] = deps.build_approval_session_bundle(
                handshake_bundle=handshake,
                plan_bundle=plan_bundle,
                workspace_id=str(workspace_id or ""),
                request_id=str(deps.get_request_id(http) or ""),
            )
            resp.diagnostics["durable_approval_session_contract_version"] = deps.durable_approval_session_contract_version
            resp.diagnostics["assistant_durable_approval_session"] = deps.build_durable_approval_session_record(
                approval_session_bundle=dict(resp.diagnostics.get("assistant_approval_session") or {}),
                session_id=str(getattr(req, "session_id", "") or "default"),
                confirmation_token=str(handshake.get("confirmation_token", "") or ""),
                transition_input=transition_input,
                previous_record=loaded_durable_approval,
            )
            resp.diagnostics["idempotency_record_contract_version"] = deps.idempotency_record_contract_version
            resp.diagnostics["assistant_idempotency_record"] = deps.build_idempotency_record_snapshot(
                execution_idempotency_bundle=execution_idempotency,
                workspace_id=str(workspace_id or ""),
                plan_id=str(plan_bundle.get("plan_id", "") or ""),
                transition_input=transition_input,
            )
    except Exception as exc:
        resp.diagnostics = deps.append_planning_reason_codes(
            diagnostics=dict(getattr(resp, "diagnostics", None) or {}),
            reason_codes=["answer_service_post_orchestration_soft_failure"],
        )
        deps.logger.warning(
            "Answer service soft-failure: post-orchestration wiring skipped",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_service_post_orchestration_soft_failure",
            },
        )
    return resp
