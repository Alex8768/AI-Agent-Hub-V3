from __future__ import annotations

from typing import Any

from fastapi import Request

from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.governance.subcore import build_governance_subcore_bundle
from src.layers.pro.reasoning.contracts import (
    ADAPTATION_CONTRACT_VERSION,
    AnswerRequest,
    APPROVAL_SESSION_CONTRACT_VERSION,
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
from src.services.answer.reasoning.llm_planner_policy import (
    apply_feedback_adaptation_policy_guards as _apply_feedback_adaptation_policy_guards,
    apply_feedback_policy_guards as _apply_feedback_policy_guards,
    apply_llm_planner_policy_guards as _apply_llm_planner_policy_guards,
    apply_plan_policy_guards as _apply_plan_policy_guards,
    apply_tool_selection_policy_guards as _apply_tool_selection_policy_guards,
    build_feedback_adaptation_policy_contract as _build_feedback_adaptation_policy_contract,
    build_feedback_policy_contract as _build_feedback_policy_contract,
    build_llm_planner_policy_contract as _build_llm_planner_policy_contract,
    build_tool_selection_policy_contract as _build_tool_selection_policy_contract,
)

async def apply_answer_diagnostics(
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
    _build_planner_runtime_parity_fallback_bundle: object,
    _infer_assistant_intent: object,
    _build_planner_with_fallback: object,
    _load_mcp_tools_from_runtime: object,
    _build_tool_selection_bundle: object,
    _build_feedback_learning_bundle: object,
    _build_feedback_adaptation_bundle: object,
    _run_assistant_execution_orchestration_seam: object,
    _append_planning_reason_codes: object,
    _wire_runtime_diagnostics: object,
    _build_memory_consistency_bundle: object,
    _build_memory_consistency_strategy_contract: object,
    _build_deterministic_plan: object,
    _LLM_PLANNER_ALLOWED_INTENTS: object,
    EXECUTION_GATEWAY_CONTRACT_VERSION: object,
    _LOGGER: object,
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

