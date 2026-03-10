from __future__ import annotations

import json
import pytest

from src.services.answer.answer_service import AnswerService
from src.layers.pro.reasoning.contracts import AnswerRequest


class _DummyState:
    def __init__(self, request_id: str):
        self.request_id = request_id


class _DummyAppState:
    def __init__(self, rag_engine: object, hybrid_retriever: object):
        self.rag_engine = rag_engine
        self.hybrid_retriever = hybrid_retriever


class _DummyApp:
    def __init__(self, state: _DummyAppState):
        self.state = state


class _DummyHTTP:
    def __init__(self, *, request_id: str, rag_engine: object, hybrid_retriever: object):
        self.state = _DummyState(request_id)
        self.headers = {}
        self.app = _DummyApp(_DummyAppState(rag_engine, hybrid_retriever))


class _FakeHybrid:
    async def retrieve(
        self,
        *,
        engine,
        workspace_id,
        query,
        k,
        filters,
        similarity_threshold,
        graph_depth,
        evidence_max_total,
        evidence_max_chunks,
        evidence_max_memory,
        evidence_max_edges,
        evidence_dedupe,
        evidence_rerank,
    ):
        # minimal evidence with chunk_id so top_evidence becomes chunk:<id>
        return {
            "graph": {"nodes": [], "edges": []},
            "results": [{"id": "r1"}],
            "evidence": [{"chunk_id": "c1", "text": "hello"}],
            "stats": {"vector_candidates_count": 1, "evidence_policy_evidence_after_policy_count": 1},
        }


class _CaptureHybrid:
    def __init__(self):
        self.kwargs = {}

    async def retrieve(self, **kwargs):
        self.kwargs = dict(kwargs or {})
        return {"graph": {"nodes": [], "edges": []}, "results": [], "evidence": [], "stats": {}}


class _FakeResp:
    def __init__(self):
        self.answer = "ok"
        self.diagnostics = {}
        self.timings = {}
        self.provenance = []
        self.used_chunks = ['c1']
        self.used_nodes = []
        self.used_edges = []


class _FakeReasoningEngine:
    def __init__(self, retriever):
        self._retriever = retriever

    async def synthesize(self, req):
        # Ensure retriever runs to populate retriever.last_top_evidence
        await self._retriever.retrieve(req)
        return _FakeResp()


class _ProbeReasoningEngine:
    def __init__(self):
        self.last_req = None

    async def synthesize(self, req):
        self.last_req = req
        return _FakeResp()


@pytest.mark.asyncio
async def test_answer_service_populates_debug_snapshot_fields(monkeypatch):
    # --- settings flags ---
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())

    # --- trace id ---
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    # --- providers.get_reasoning_engine should return our fake engine ---
    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return _FakeReasoningEngine(retriever)

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="x", k=8, graph_depth=1, filters={})

    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    assert set(diag.keys()) == {
        "retrieved_provenance_count",
        "used_chunks_count",
        "used_nodes_count",
        "used_edges_count",
        "has_llm",
        "query_len",
        "k",
        "graph_depth",
        "session_id",
        "evidence_contract_version",
        "evidence_contract_valid_minimal",
        "evidence_contract_missing_minimal_fields",
        "evidence_contract_missing_minimal_count",
        "evidence_contract_minimal_coverage_score",
        "evidence_contract_gate_reason",
        "self_check",
        "reasoning_execution_policy",
        "reasoning_quality",
        "reasoning_benchmark",
        "reasoning_optimization",
        "enterprise_productization",
        "meta_cognition",
        "reasoning_trace",
        "anticipatory",
        "reasoning_timeline",
        "verify",
        "planner_runtime_parity",
        "session_memory_loaded",
        "session_memory_hit",
        "memory_consistency",
        "memory_consistency_strategy",
        "governance_subcore",
        "evidence_type_counts",
        "top_evidence",
        "trace_id",
        "llm_enabled",
        "llm_provider",
        "llm_model",
        "llm_error",
        "assistant_contract_version",
        "response_mode",
        "response_language",
        "assistant_recovery_policy",
        "assistant_mode_enabled",
        "assistant_proactive_enabled",
        "assistant_actions_enabled",
        "intent_contract_version",
        "plan_contract_version",
        "llm_planner_contract_version",
        "tool_selection_contract_version",
        "assistant_intent",
        "assistant_plan",
        "assistant_llm_planner",
        "assistant_tool_selection",
        "tool_selection_policy",
        "feedback_contract_version",
        "assistant_feedback_learning",
        "feedback_policy",
        "adaptation_contract_version",
        "assistant_feedback_adaptation",
        "adaptation_policy",
        "llm_planner_policy",
        "planning_policy",
        "execution_handshake_contract_version",
        "assistant_execution_handshake",
        "execution_transition_policy",
        "execution_request_boundary",
        "execution_idempotency",
        "execution_receipt_contract_version",
        "assistant_execution_receipt",
        "execution_gateway_contract_version",
        "assistant_execution_gateway",
        "execution_pilot_contract_version",
        "assistant_execution_pilot",
        "approval_session_contract_version",
        "assistant_approval_session",
        "durable_approval_session_contract_version",
        "assistant_durable_approval_session",
        "idempotency_record_contract_version",
        "assistant_idempotency_record",
        "planning_reason_codes",
        "plan_id",
        "retriever_stats",
        "session_memory_saved",
    }

    # Contract keys expected by debug snapshot behavior
    assert "trace_id" in diag
    assert diag["trace_id"] in ("trace-123", "rid-1")

    assert "evidence_type_counts" in diag
    assert isinstance(diag["evidence_type_counts"], dict)

    assert "top_evidence" in diag
    assert isinstance(diag["top_evidence"], list)
    assert any(str(x).startswith("chunk:") for x in diag["top_evidence"])
    assert diag.get("intent_contract_version") == "v1"
    assert diag.get("plan_contract_version") == "v1"
    assert diag.get("llm_planner_contract_version") == "v1"
    assert diag.get("tool_selection_contract_version") == "v1"
    intent = dict(diag.get("assistant_intent") or {})
    assert set(intent.keys()) == {
        "intent",
        "confidence",
        "entities",
        "implicit_tasks",
        "source",
    }
    plan = dict(diag.get("assistant_plan") or {})
    assert set(plan.keys()) == {
        "contract_version",
        "plan_id",
        "status",
        "deterministic",
        "intent",
        "steps",
        "requires_confirmation",
        "reason_codes",
    }
    llm_planner = dict(diag.get("assistant_llm_planner") or {})
    assert set(llm_planner.keys()) == {
        "contract_version",
        "source",
        "status",
        "model",
        "intent",
        "plan_id",
        "reason_codes",
    }
    tool_selection = dict(diag.get("assistant_tool_selection") or {})
    assert set(tool_selection.keys()) == {
        "contract_version",
        "mode",
        "status",
        "source",
        "selected_tools",
        "blocked_step_ids",
        "reason_codes",
    }
    tool_selection_policy = dict(diag.get("tool_selection_policy") or {})
    assert set(tool_selection_policy.keys()) == {
        "mode",
        "allow_mcp_source",
        "allow_deterministic_fallback",
        "allowed_routes",
        "require_plan_step_binding",
        "max_selected_tools",
        "fallback_on_policy_violation",
        "violations",
        "applied_reason_codes",
    }
    assert diag.get("feedback_contract_version") == "v1"
    feedback_learning = dict(diag.get("assistant_feedback_learning") or {})
    assert set(feedback_learning.keys()) == {
        "contract_version",
        "mode",
        "status",
        "signals",
        "latest_signal",
        "signal_counts",
        "reason_codes",
    }
    feedback_policy = dict(diag.get("feedback_policy") or {})
    assert set(feedback_policy.keys()) == {
        "mode",
        "allowed_signals",
        "max_signals_per_request",
        "require_latest_in_signals",
        "fallback_on_policy_violation",
        "violations",
        "applied_reason_codes",
    }
    assert diag.get("adaptation_contract_version") == "v1"
    feedback_adaptation = dict(diag.get("assistant_feedback_adaptation") or {})
    assert set(feedback_adaptation.keys()) == {
        "contract_version",
        "mode",
        "status",
        "source",
        "latest_signal",
        "boosted_intents",
        "suppressed_intents",
        "reason_codes",
    }
    adaptation_policy = dict(diag.get("adaptation_policy") or {})
    assert set(adaptation_policy.keys()) == {
        "mode",
        "allowed_latest_signals",
        "allowed_intents",
        "max_boosted_intents",
        "max_suppressed_intents",
        "forbid_boost_suppress_overlap",
        "fallback_on_policy_violation",
        "violations",
        "applied_reason_codes",
    }
    llm_planner_policy = dict(diag.get("llm_planner_policy") or {})
    assert set(llm_planner_policy.keys()) == {
        "mode",
        "allow_llm_source",
        "allowed_intents",
        "require_plan_id_prefix_match",
        "fallback_on_policy_violation",
        "violations",
        "applied_reason_codes",
    }
    policy = dict(diag.get("planning_policy") or {})
    assert set(policy.keys()) == {
        "mode",
        "max_steps",
        "blocked_steps_count",
        "truncated",
        "allowed_action_pattern",
        "reason_codes",
    }
    assert diag.get("execution_handshake_contract_version") == "v1"
    handshake = dict(diag.get("assistant_execution_handshake") or {})
    assert set(handshake.keys()) == {
        "contract_version",
        "state",
        "requires_confirmation",
        "confirmation_token",
        "approved_action_ids",
        "blocked_action_ids",
        "receipt_id",
        "reason_codes",
    }
    transition_policy = dict(diag.get("execution_transition_policy") or {})
    assert set(transition_policy.keys()) == {
        "mode",
        "require_confirmation_token",
        "allow_partial_approval",
        "max_approved_action_ids",
        "allowlisted_action_types",
        "allowlisted_action_pattern",
        "enforce_allowlisted_action_types",
        "allowed_decisions",
        "requested_action_ids_count",
        "available_action_ids_count",
        "unknown_action_ids",
        "blocked_non_allowlisted_action_ids",
        "rollback_contract_status",
        "rollback_missing_action_ids",
        "applied_reason_codes",
    }
    execution_request_boundary = dict(diag.get("execution_request_boundary") or {})
    assert set(execution_request_boundary.keys()) == {
        "contract_version",
        "mode",
        "status",
        "decision",
        "requested_action_ids_count",
        "has_confirmation_token",
        "idempotency_key_present",
        "transition_policy_mode",
        "reason_codes",
    }
    idempotency = dict(diag.get("execution_idempotency") or {})
    assert set(idempotency.keys()) == {
        "contract_version",
        "status",
        "idempotency_key",
        "operation_fingerprint",
        "guard_action",
        "reason_codes",
    }
    assert diag.get("execution_receipt_contract_version") == "v1"
    receipt = dict(diag.get("assistant_execution_receipt") or {})
    assert set(receipt.keys()) == {
        "contract_version",
        "receipt_id",
        "status",
        "handshake_state",
        "plan_id",
        "approved_action_ids",
        "blocked_action_ids",
        "executed_action_ids",
        "rollback_status",
        "rollback_required_action_ids",
        "rollback_ready_action_ids",
        "rollback_missing_action_ids",
        "reason_codes",
    }
    assert diag.get("execution_gateway_contract_version") == "v1"
    gateway = dict(diag.get("assistant_execution_gateway") or {})
    assert set(gateway.keys()) == {
        "contract_version",
        "mode",
        "state",
        "safe_mode",
        "approved_action_ids",
        "blocked_action_ids",
        "executed_action_ids",
        "dry_run_action_ids",
        "reason_codes",
    }
    assert diag.get("execution_pilot_contract_version") == "v1"
    pilot = dict(diag.get("assistant_execution_pilot") or {})
    assert set(pilot.keys()) == {
        "contract_version",
        "mode",
        "state",
        "safe_mode",
        "execute_enabled",
        "max_actions_per_run",
        "allowed_action_types",
        "requested_action_ids",
        "eligible_action_ids",
        "blocked_action_ids",
        "executed_action_ids",
        "reason_codes",
    }
    assert diag.get("approval_session_contract_version") == "v1"
    approval = dict(diag.get("assistant_approval_session") or {})
    assert set(approval.keys()) == {
        "contract_version",
        "approval_id",
        "workspace_id",
        "plan_id",
        "status",
        "requires_confirmation",
        "one_time_token",
        "token_ttl_seconds",
        "reason_codes",
    }
    assert diag.get("durable_approval_session_contract_version") == "v1"
    durable_approval = dict(diag.get("assistant_durable_approval_session") or {})
    assert set(durable_approval.keys()) == {
        "contract_version",
        "approval_id",
        "workspace_id",
        "session_id",
        "plan_id",
        "status",
        "confirmation_token",
        "token_expires_at",
        "last_decision",
        "reason_codes",
    }
    assert diag.get("idempotency_record_contract_version") == "v1"
    idempotency_record = dict(diag.get("assistant_idempotency_record") or {})
    assert set(idempotency_record.keys()) == {
        "contract_version",
        "idempotency_key",
        "workspace_id",
        "plan_id",
        "operation_fingerprint",
        "status",
        "confirmation_token",
        "decision",
        "reason_codes",
    }
    assert isinstance(diag.get("planning_reason_codes"), list)
    assert isinstance(diag.get("plan_id"), str)
    assert diag.get("session_id") == "default"
    memory_consistency = dict(diag.get("memory_consistency") or {})
    assert set(memory_consistency.keys()) == {
        "contract_version",
        "mode",
        "status",
        "inputs",
        "reason_codes",
    }
    assert memory_consistency.get("contract_version") == "v1"
    assert memory_consistency.get("mode") == "memory_consistency_guarded"
    assert memory_consistency.get("status") in {"ok", "warn"}
    memory_inputs = dict(memory_consistency.get("inputs") or {})
    assert set(memory_inputs.keys()) == {
        "session_memory_loaded",
        "session_memory_hit",
        "durable_approval_record_loaded",
        "durable_idempotency_record_loaded",
    }
    memory_strategy = dict(diag.get("memory_consistency_strategy") or {})
    assert set(memory_strategy.keys()) == {
        "contract_version",
        "mode",
        "consistency_target",
        "write_strategy",
        "outbox_strategy",
        "compensation_strategy",
        "reason_codes",
    }
    assert memory_strategy.get("contract_version") == "v1"
    assert memory_strategy.get("mode") == "best_effort_dual_store"
    governance_subcore = dict(diag.get("governance_subcore") or {})
    assert set(governance_subcore.keys()) == {
        "contract_version",
        "mode",
        "status",
        "trace_status",
        "timeline_status",
        "receipt_status",
        "replay_status",
        "reason_codes",
    }
    assert governance_subcore.get("contract_version") == "v1"
    assert governance_subcore.get("mode") == "governance_subcore"
    assert diag.get("evidence_contract_version") == "v1"
    assert isinstance(diag.get("evidence_contract_valid_minimal"), bool)
    assert isinstance(diag.get("evidence_contract_missing_minimal_fields"), list)
    assert isinstance(diag.get("evidence_contract_missing_minimal_count"), int)
    assert isinstance(diag.get("evidence_contract_minimal_coverage_score"), float)
    assert isinstance(diag.get("evidence_contract_gate_reason"), str)
    sc = dict(diag.get("self_check") or {})
    assert sc.get("version") == "v1"
    assert sc.get("status") == "warn"
    assert sc.get("reasons") == ["threshold:minimal_coverage_score<1.0"]
    assert sc.get("policy_mode") == "warning_only"
    sc_inputs = dict(sc.get("inputs") or {})
    assert set(sc_inputs.keys()) == {
        "evidence_contract_valid_minimal",
        "evidence_contract_missing_minimal_count",
        "evidence_contract_minimal_coverage_score",
    }
    assert sc_inputs.get("evidence_contract_valid_minimal") is False
    assert sc_inputs.get("evidence_contract_missing_minimal_count") == 0
    planner_parity = dict(diag.get("planner_runtime_parity") or {})
    assert set(planner_parity.keys()) == {
        "contract_version",
        "mode",
        "status",
        "inputs",
        "thresholds",
        "reason_codes",
    }
    assert planner_parity.get("contract_version") == "v1"
    assert planner_parity.get("mode") == "planner_runtime_parity_guarded"
    assert sc_inputs.get("evidence_contract_minimal_coverage_score") == 0.0
    sc_thresholds = dict(sc.get("thresholds") or {})
    assert sc_thresholds.get("minimal_coverage_score_min") == 1.0
    assert sc_thresholds.get("missing_minimal_count_max") == 0
    verify = dict(diag.get("verify") or {})
    assert verify.get("version") == "v1"
    assert verify.get("status") == "warn"
    assert verify.get("reasons") == [
        "self_check_status!=pass",
        "self_check_reasons_count>0",
    ]
    assert verify.get("policy_mode") == "warning_only"
    v_inputs = dict(verify.get("inputs") or {})
    assert set(v_inputs.keys()) == {
        "planner_path_used",
        "self_check_status",
        "self_check_policy_mode",
        "self_check_reasons_count",
    }
    assert v_inputs.get("planner_path_used") is False
    assert v_inputs.get("self_check_status") == "warn"
    assert v_inputs.get("self_check_policy_mode") == "warning_only"
    assert v_inputs.get("self_check_reasons_count") == 1
    v_thr = dict(verify.get("thresholds") or {})
    assert set(v_thr.keys()) == {
        "required_self_check_status",
        "required_self_check_policy_mode",
        "self_check_reasons_count_max",
    }
    assert v_thr.get("required_self_check_status") == "pass"
    assert v_thr.get("required_self_check_policy_mode") == "warning_only"
    assert v_thr.get("self_check_reasons_count_max") == 0
    rep = dict(diag.get("reasoning_execution_policy") or {})
    assert set(rep.keys()) == {"max_steps", "max_latency_ms", "max_retries"}
    assert isinstance(rep.get("max_steps"), int)
    assert isinstance(rep.get("max_latency_ms"), int)
    assert isinstance(rep.get("max_retries"), int)
    rq = dict(diag.get("reasoning_quality") or {})
    assert rq.get("version") == "v1"
    assert isinstance(rq.get("claims_total"), int)
    assert isinstance(rq.get("claims_sample"), list)
    rq_cov = dict(rq.get("coverage") or {})
    assert set(rq_cov.keys()) == {
        "claims_total",
        "claims_covered",
        "claims_uncovered",
        "coverage_score",
        "covered_claim_indices",
        "uncovered_claim_indices",
    }
    rq_conf = dict(rq.get("confidence") or {})
    assert set(rq_conf.keys()) == {
        "coverage_score",
        "unsupported_claims",
        "missing_claims",
        "penalty_unsupported",
        "penalty_missing",
        "penalty_total",
        "raw_confidence",
        "confidence_score",
    }
    rq_retry = dict(rq.get("retry") or {})
    assert set(rq_retry.keys()) == {
        "attempt",
        "max_retries",
        "confidence_score",
        "threshold",
        "confidence_below_threshold",
        "retry_budget_available",
        "should_retry",
        "next_attempt",
        "loop_guard_triggered",
        "reason",
    }
    rb = dict(diag.get("reasoning_benchmark") or {})
    assert set(rb.keys()) == {
        "suite_name",
        "summary",
        "failed_case_ids",
        "average_latency_ms",
        "results",
    }
    rb_summary = dict(rb.get("summary") or {})
    assert set(rb_summary.keys()) == {
        "suite_name",
        "total_cases",
        "passed_cases",
        "pass_rate",
        "average_score",
        "results",
    }
    ro = dict(diag.get("reasoning_optimization") or {})
    assert set(ro.keys()) == {"signal", "proposals", "decision"}
    ro_signal = dict(ro.get("signal") or {})
    assert set(ro_signal.keys()) == {
        "trace_id",
        "confidence_score",
        "coverage_score",
        "pass_rate",
        "average_latency_ms",
        "warnings_count",
        "retry_rate",
        "signal_tags",
    }
    assert isinstance(ro.get("proposals"), list)
    ro_decision = dict(ro.get("decision") or {})
    assert set(ro_decision.keys()) == {
        "decision_id",
        "action",
        "selected_proposal_ids",
        "reason_codes",
        "confidence",
        "requires_human_review",
    }
    ep = dict(diag.get("enterprise_productization") or {})
    assert set(ep.keys()) == {
        "release_gate_policy",
        "release_checks",
        "readiness",
        "rollout_decision",
    }
    ep_policy = dict(ep.get("release_gate_policy") or {})
    assert set(ep_policy.keys()) == {
        "profile_name",
        "required_checks",
        "blocking_checks",
        "minimum_pass_rate",
        "minimum_average_score",
        "minimum_coverage_ratio",
        "allow_skipped",
        "require_benchmark_summary",
        "require_optimization_review",
        "allowed_warning_codes",
    }
    assert isinstance(ep.get("release_checks"), dict)
    ep_readiness = dict(ep.get("readiness") or {})
    assert set(ep_readiness.keys()) == {
        "profile_name",
        "release_gate_passed",
        "failed_checks",
        "benchmark_pass_rate",
        "benchmark_average_score",
        "optimization_action",
        "optimization_requires_review",
        "warnings_count",
        "readiness_score",
        "reason_codes",
    }
    ep_rollout = dict(ep.get("rollout_decision") or {})
    assert set(ep_rollout.keys()) == {
        "decision_id",
        "action",
        "target_environment",
        "blocked_by",
        "reason_codes",
        "confidence",
        "requires_human_approval",
    }
    mc = dict(diag.get("meta_cognition") or {})
    assert set(mc.keys()) == {"uncertainty", "gap_map", "reflection"}
    mc_uncertainty = dict(mc.get("uncertainty") or {})
    assert set(mc_uncertainty.keys()) == {
        "status",
        "uncertainty_score",
        "signals",
        "reason_codes",
        "warnings",
    }
    mc_gap_map = dict(mc.get("gap_map") or {})
    assert set(mc_gap_map.keys()) == {
        "session_id",
        "status",
        "total_gaps",
        "high_priority_gaps",
        "coverage_score",
        "gaps",
        "reason_codes",
        "warnings",
    }
    mc_reflection = dict(mc.get("reflection") or {})
    assert set(mc_reflection.keys()) == {
        "status",
        "confidence_score",
        "uncertainty_score",
        "coverage_score",
        "insight_count",
        "insights",
        "reason_codes",
        "warnings",
    }
    rt = dict(diag.get("reasoning_trace") or {})
    assert set(rt.keys()) == {
        "query",
        "plan",
        "steps",
        "verify_results",
        "quality",
        "timeline",
        "answer",
    }
    assert isinstance(rt.get("query"), str)
    assert isinstance(rt.get("plan"), list)
    assert isinstance(rt.get("steps"), list)
    assert isinstance(rt.get("verify_results"), list)
    assert isinstance(rt.get("quality"), dict)
    assert isinstance(rt.get("timeline"), dict)
    assert isinstance(rt.get("answer"), str)
    tl = dict(diag.get("reasoning_timeline") or {})
    assert set(tl.keys()) == {"events", "total_duration_ms"}
    assert isinstance(tl.get("events"), list)
    assert isinstance(tl.get("total_duration_ms"), int)
    ant = dict(diag.get("anticipatory") or {})
    assert set(ant.keys()) == {
        "whisper_receipt",
        "opportunity_scan",
        "proactive_suggestions",
        "draft_actions",
    }
    ant_receipt = dict(ant.get("whisper_receipt") or {})
    assert set(ant_receipt.keys()) == {
        "run_id",
        "status",
        "safe_mode",
        "duration_ms",
        "suggestion_count",
        "reason_codes",
        "warnings",
    }
    ant_scan = dict(ant.get("opportunity_scan") or {})
    assert set(ant_scan.keys()) == {
        "status",
        "opportunity_score",
        "signals",
        "reason_codes",
        "warnings",
    }
    ant_suggestions = dict(ant.get("proactive_suggestions") or {})
    assert set(ant_suggestions.keys()) == {
        "status",
        "suggestions",
        "top_suggestion_id",
        "reason_codes",
        "warnings",
    }
    ant_actions = dict(ant.get("draft_actions") or {})
    assert set(ant_actions.keys()) == {
        "status",
        "actions",
        "top_action_id",
        "requires_confirmation",
        "reason_codes",
        "warnings",
    }
    rs = (diag.get("retriever_stats") or {})
    assert rs.get("evidence_policy_evidence_after_policy_count") == 1


@pytest.mark.asyncio
async def test_answer_service_forwards_evidence_policy_controls(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return _FakeReasoningEngine(retriever)

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    cap = _CaptureHybrid()
    http = _DummyHTTP(request_id="rid-2", rag_engine=object(), hybrid_retriever=cap)
    req = AnswerRequest(
        query="x",
        k=8,
        graph_depth=1,
        filters={},
        evidence_max_total=17,
        evidence_max_chunks=5,
        evidence_max_memory=3,
        evidence_max_edges=2,
        evidence_dedupe=False,
        evidence_rerank=False,
    )
    await AnswerService().handle(http, req, workspace_id="default")

    assert cap.kwargs.get("evidence_max_total") == 17
    assert cap.kwargs.get("evidence_max_chunks") == 5
    assert cap.kwargs.get("evidence_max_memory") == 3
    assert cap.kwargs.get("evidence_max_edges") == 2
    assert cap.kwargs.get("evidence_dedupe") is False
    assert cap.kwargs.get("evidence_rerank") is False


@pytest.mark.asyncio
async def test_answer_service_saves_session_memory_best_effort(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return _FakeReasoningEngine(retriever)

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    calls = {}

    class _Mem:
        async def put(self, *, workspace_id, key, value, metadata=None):
            calls["workspace_id"] = workspace_id
            calls["key"] = key
            calls["value"] = value
            calls["metadata"] = dict(metadata or {})

    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: _Mem())

    http = _DummyHTTP(request_id="rid-3", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="what?", session_id="s-1")
    resp = await AnswerService().handle(http, req, workspace_id="default")

    assert calls.get("workspace_id") == "default"
    assert calls.get("key") == "session:s-1:last_answer"
    assert calls.get("value") == "ok"
    assert (calls.get("metadata") or {}).get("session_id") == "s-1"
    assert (calls.get("metadata") or {}).get("query") == "what?"
    assert (getattr(resp, "diagnostics", {}) or {}).get("session_memory_saved") is True


@pytest.mark.asyncio
async def test_answer_service_loads_session_memory_before_reasoning(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    probe = _ProbeReasoningEngine()

    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return probe

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    class _Mem:
        async def get(self, *, workspace_id, key):
            assert workspace_id == "default"
            assert key == "session:s-42:last_answer"
            return "previous turn answer"

        async def put(self, *, workspace_id, key, value, metadata=None):
            return None

    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: _Mem())

    http = _DummyHTTP(request_id="rid-4", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="follow up", session_id="s-42")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert probe.last_req is not None
    assert getattr(probe.last_req, "session_memory_last_answer", "") == "previous turn answer"
    assert diag.get("session_memory_loaded") is True
    assert diag.get("session_memory_hit") is True
    assert any(str(x).startswith("memory:session:s-42:last_answer") for x in (diag.get("top_evidence") or []))
    assert int((diag.get("evidence_type_counts") or {}).get("memory", 0)) >= 1


@pytest.mark.asyncio
async def test_answer_service_clips_session_memory_payload(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    long_answer = "A" * 5000
    long_prev = "B" * 5000
    calls = {}

    class _Engine:
        def __init__(self):
            self.last_req = None

        async def synthesize(self, req):
            self.last_req = req
            r = _FakeResp()
            r.answer = long_answer
            return r

    eng = _Engine()

    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return eng

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    class _Mem:
        async def get(self, *, workspace_id, key):
            return long_prev

        async def put(self, *, workspace_id, key, value, metadata=None):
            calls["value"] = value

    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: _Mem())

    http = _DummyHTTP(request_id="rid-5", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="long", session_id="s-long")
    await AnswerService().handle(http, req, workspace_id="default")

    assert len(getattr(eng.last_req, "session_memory_last_answer", "")) == 4000
    assert len(calls.get("value", "")) == 4000


@pytest.mark.asyncio
async def test_answer_service_verify_warns_when_self_check_reasons_not_empty(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    class _Resp(_FakeResp):
        def __init__(self):
            super().__init__()
            self.diagnostics = {
                "planner_path_used": True,
                "self_check": {
                    "version": "v1",
                    "status": "pass",
                    "reasons": ["manual_reason"],
                    "policy_mode": "warning_only",
                    "inputs": {},
                    "thresholds": {},
                },
            }

    class _Engine:
        async def synthesize(self, req):
            return _Resp()

    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _Engine(),
    )

    http = _DummyHTTP(request_id="rid-verify-1", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    resp = await AnswerService().handle(http, AnswerRequest(query="q"), workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    verify = dict(diag.get("verify") or {})
    assert verify.get("status") == "warn"
    assert verify.get("reasons") == ["self_check_reasons_count>0"]
    v_inputs = dict(verify.get("inputs") or {})
    assert v_inputs.get("planner_path_used") is True
    assert v_inputs.get("self_check_status") == "pass"
    assert v_inputs.get("self_check_policy_mode") == "warning_only"
    assert v_inputs.get("self_check_reasons_count") == 1

    warnings = list(getattr(resp, "warnings", []) or [])
    assert "verify_warning" in warnings


@pytest.mark.asyncio
async def test_answer_service_assistant_fallback_localizes_russian(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-assistant-ru", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="Привет, кто ты?")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert "Привет!" in str(getattr(resp, "answer", ""))
    assert diag.get("response_mode") == "assistant_fallback"
    assert diag.get("response_language") == "ru"
    recovery_policy = dict(diag.get("assistant_recovery_policy") or {})
    assert set(recovery_policy.keys()) == {
        "mode",
        "allow_low_evidence_only",
        "allowed_intents",
        "block_greeting_queries",
        "allowed_languages",
        "require_assistant_mode",
        "fallback_on_policy_violation",
        "target_language",
        "violations",
        "applied_reason_codes",
    }
    assert "assistant_chat_recovery_greeting_blocked" in list(recovery_policy.get("violations") or [])
    assert "assistant_chat_recovery_policy_forced_fallback" in list(recovery_policy.get("applied_reason_codes") or [])
    assert diag.get("assistant_mode_enabled") is True


@pytest.mark.asyncio
async def test_answer_service_assistant_fallback_localizes_english(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-assistant-en", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="Hi, who are you?")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert "Hi!" in str(getattr(resp, "answer", ""))
    assert diag.get("response_mode") == "assistant_fallback"
    assert diag.get("response_language") == "en"
    assert diag.get("assistant_mode_enabled") is True


@pytest.mark.asyncio
async def test_answer_service_applies_chat_recovery_for_low_evidence_non_greeting(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    async def _fake_chat_recovery(**kwargs):
        _ = kwargs
        return "Да, конечно. Я готова помогать."

    monkeypatch.setattr("src.services.answer.answer_service._build_assistant_chat_recovery_answer", _fake_chat_recovery)

    http = _DummyHTTP(request_id="rid-assistant-chat-recovery", rag_engine=object(), hybrid_retriever=_CaptureHybrid())
    req = AnswerRequest(query="Ты готова мне помогать и обучаться?")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert "готова помогать" in str(getattr(resp, "answer", "")).lower()
    assert diag.get("assistant_chat_recovery_applied") is True
    assert "assistant_chat_recovery_applied" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_normalizes_unknown_low_evidence_friendliness(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    async def _fake_chat_recovery(**kwargs):
        _ = kwargs
        return "Извините, я не знаю."

    monkeypatch.setattr("src.services.answer.answer_service._build_assistant_chat_recovery_answer", _fake_chat_recovery)

    http = _DummyHTTP(request_id="rid-assistant-friendly-normalize", rag_engine=object(), hybrid_retriever=_CaptureHybrid())
    req = AnswerRequest(query="Ты готова помочь с задачей?")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert "извините, я не знаю" not in str(getattr(resp, "answer", "")).lower()
    assert "assistant_low_evidence_friendliness_applied" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_build_assistant_chat_recovery_answer_keeps_user_language(monkeypatch):
    import src.services.answer.answer_service as answer_service_module

    class _LLM:
        async def generate(self, prompt):
            _ = prompt
            # Wrong language on purpose (English for Russian query).
            return "Yes, I can help with that."

    out = await answer_service_module._build_assistant_chat_recovery_answer(
        query="Ты готова помогать?",
        language="ru",
        llm=_LLM(),
        current_answer="Извините, я не знаю.",
    )
    assert "Да, конечно" in out


@pytest.mark.asyncio
async def test_answer_service_recovery_policy_blocks_recovery_for_greeting(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    async def _fake_chat_recovery(**kwargs):
        _ = kwargs
        return "Этот текст не должен применяться"

    monkeypatch.setattr("src.services.answer.answer_service._build_assistant_chat_recovery_answer", _fake_chat_recovery)

    http = _DummyHTTP(request_id="rid-assistant-recovery-policy-greeting", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="Привет, ты тут?")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    policy = dict(diag.get("assistant_recovery_policy") or {})

    assert "assistant_chat_recovery_greeting_blocked" in list(policy.get("violations") or [])
    assert "assistant_chat_recovery_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])
    assert diag.get("assistant_chat_recovery_applied") is not True


@pytest.mark.asyncio
async def test_answer_service_proactive_ranking_mvp(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = True
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    async def _fake_anticipatory(**kwargs):
        return {
            "whisper_receipt": {"status": "ok"},
            "opportunity_scan": {"status": "active"},
            "proactive_suggestions": {
                "status": "active",
                "suggestions": [
                    {"suggestion_id": "s-low", "suggestion_type": "follow_up", "confidence": 0.2},
                    {"suggestion_id": "s-high", "suggestion_type": "automation", "confidence": 0.9},
                    {"suggestion_id": "s-mid", "suggestion_type": "summarization", "confidence": 0.6},
                ],
                "top_suggestion_id": "s-low",
                "reason_codes": ["suggestions_available"],
                "warnings": [],
            },
        }

    monkeypatch.setattr("src.services.answer.answer_service._run_anticipatory_safe_mode", _fake_anticipatory)

    http = _DummyHTTP(request_id="rid-assistant-rank", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="prepare project", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    proactive = dict((dict(diag.get("anticipatory") or {})).get("proactive_suggestions") or {})
    actions = dict((dict(diag.get("anticipatory") or {})).get("draft_actions") or {})
    rows = list(proactive.get("suggestions") or [])

    assert [str((row or {}).get("suggestion_id", "")) for row in rows] == ["s-high", "s-mid", "s-low"]
    assert [int((row or {}).get("rank", 0) or 0) for row in rows] == [1, 2, 3]
    assert [int((row or {}).get("priority", -1) or -1) for row in rows] == [90, 60, 20]
    assert proactive.get("top_suggestion_id") == "s-high"
    assert "ranked_by_priority" in list(proactive.get("reason_codes") or [])
    assert actions.get("status") == "ready"
    assert actions.get("requires_confirmation") is True
    action_rows = list(actions.get("actions") or [])
    assert [str((row or {}).get("action_id", "")) for row in action_rows] == [
        "draft_action:s-high",
        "draft_action:s-mid",
        "draft_action:s-low",
    ]
    assert actions.get("top_action_id") == "draft_action:s-high"
    assert "draft_actions_available" in list(actions.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_proactive_disabled_adds_reason_code(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-assistant-proactive-off", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="prepare project", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    proactive = dict((dict(diag.get("anticipatory") or {})).get("proactive_suggestions") or {})
    actions = dict((dict(diag.get("anticipatory") or {})).get("draft_actions") or {})
    assert "assistant_proactive_disabled" in list(proactive.get("reason_codes") or [])
    assert actions.get("status") == "disabled"
    assert actions.get("actions") == []
    assert "assistant_actions_disabled" in list(actions.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_builds_deterministic_plan_for_project_intent(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-plan-project", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="Мне дали проект ББРР 2026", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    plan = dict(diag.get("assistant_plan") or {})
    steps = list(plan.get("steps") or [])

    assert diag.get("assistant_mode_enabled") is True
    assert diag.get("plan_contract_version") == "v1"
    assert plan.get("status") == "ready"
    assert plan.get("deterministic") is True
    assert str(plan.get("plan_id", "")).startswith("plan:start_project:")
    assert diag.get("plan_id") == plan.get("plan_id")
    assert plan.get("requires_confirmation") is True
    assert len(steps) >= 2
    assert [str((row or {}).get("step_id", "")) for row in steps][:2] == ["step:1", "step:2"]
    assert "deterministic_plan_built" in list(plan.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_uses_llm_planner_adapter_with_deterministic_plan_fallback(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = True
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "openai"
        openai_model = "gpt-4o-mini"
        ollama_model = ""

    class _Completion:
        def __init__(self, content: str):
            self.content = content

    class _Provider:
        async def complete(self, *, messages, config=None):
            return _Completion("start_project")

    async def _fake_get_llm_provider():
        return _Provider()

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr("src.api.dependencies_impl.get_llm_provider", _fake_get_llm_provider)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-plan-llm-adapter", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="Нужна помощь с новым проектом", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    planner = dict(diag.get("assistant_llm_planner") or {})
    plan = dict(diag.get("assistant_plan") or {})

    assert planner.get("source") == "llm"
    assert planner.get("status") == "ready"
    assert planner.get("model") == "gpt-4o-mini"
    assert planner.get("intent") == "start_project"
    assert "llm_planner_adapter_selected_intent" in list(planner.get("reason_codes") or [])
    assert str(plan.get("plan_id", "")).startswith("plan:start_project:")
    assert "deterministic_plan_built" in list(plan.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_tool_selection_uses_mcp_registry_with_fallback(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    class _Registry:
        def list_tools(self, *, enabled_only=False, server_name=None):
            _ = enabled_only, server_name
            return [
                {
                    "tool_name": "workspace_manager",
                    "server_name": "filesystem",
                    "description": "prepare project workspace draft",
                    "tags": ["workspace", "project", "draft"],
                    "enabled": True,
                }
            ]

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-tool-select-mcp", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    http.app.state.mcp_registry = _Registry()
    req = AnswerRequest(query="new project planning", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    tool_selection = dict(diag.get("assistant_tool_selection") or {})
    selected = list(tool_selection.get("selected_tools") or [])

    assert tool_selection.get("status") == "ready"
    assert tool_selection.get("source") == "mcp"
    assert any(str((row or {}).get("tool_name", "")) == "workspace_manager" for row in selected)
    assert "tool_selection_adapter_applied" in list(tool_selection.get("reason_codes") or [])
    assert "tool_selection_mcp_matched" in list(tool_selection.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_tool_selection_policy_forces_fallback_on_violation(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    def _invalid_tool_selection(**kwargs):
        _ = kwargs
        return {
            "contract_version": "v1",
            "mode": "mcp_aware_selector",
            "status": "ready",
            "source": "mcp",
            "selected_tools": [
                {
                    "step_id": "step:unknown",
                    "tool_name": "danger_tool",
                    "route": "unknown_route",
                    "reason": "invalid_for_policy_test",
                }
            ],
            "blocked_step_ids": [],
            "reason_codes": ["tool_selection_adapter_applied"],
        }

    monkeypatch.setattr("src.services.answer.answer_service._build_tool_selection_bundle", _invalid_tool_selection)

    http = _DummyHTTP(request_id="rid-tool-select-policy", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="new project planning", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    selection = dict(diag.get("assistant_tool_selection") or {})
    policy = dict(diag.get("tool_selection_policy") or {})

    assert selection.get("source") == "deterministic"
    assert "tool_selection_policy_forced_fallback" in list(selection.get("reason_codes") or [])
    assert "tool_selection_step_not_in_plan" in list(policy.get("violations") or [])
    assert "tool_selection_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_feedback_capture_adapter_normalizes_signals(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-feedback-normalize", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(
        query="feedback normalization test",
        session_id="default",
        filters={
            "feedback_signals": ["approve", "approve", "UNKNOWN"],
            "feedback_events": [{"signal": "cancel"}, {"signal": "edit"}],
            "feedback_signal": "approve",
            "handshake_decision": "edit",
            "feedback_edit_payload": {"note": "update action order"},
        },
    )
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    feedback = dict(diag.get("assistant_feedback_learning") or {})

    assert feedback.get("signals") == ["approve", "cancel", "edit"]
    assert feedback.get("latest_signal") == "edit"
    assert feedback.get("signal_counts") == {"approve": 1, "cancel": 1, "edit": 1}
    assert "feedback_capture_adapter_normalized" in list(feedback.get("reason_codes") or [])
    assert "feedback_signal_detected:edit" in list(feedback.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_feedback_policy_forces_fallback_on_violation(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    def _invalid_feedback_bundle(**kwargs):
        _ = kwargs
        return {
            "contract_version": "v1",
            "mode": "approve_cancel_edit_feedback",
            "status": "ready",
            "signals": ["approve", "unknown", "cancel", "edit"],
            "latest_signal": "unknown",
            "signal_counts": {"approve": 1, "cancel": 1, "edit": 1},
            "reason_codes": ["feedback_capture_adapter_normalized"],
        }

    monkeypatch.setattr("src.services.answer.answer_service._build_feedback_learning_bundle", _invalid_feedback_bundle)

    http = _DummyHTTP(request_id="rid-feedback-policy", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="feedback policy test", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    feedback = dict(diag.get("assistant_feedback_learning") or {})
    policy = dict(diag.get("feedback_policy") or {})

    assert feedback.get("signals") == ["approve", "cancel", "edit"]
    assert feedback.get("latest_signal") == "edit"
    assert "feedback_policy_forced_fallback" in list(feedback.get("reason_codes") or [])
    assert "feedback_signal_not_allowlisted" in list(policy.get("violations") or [])
    assert "feedback_signals_exceed_max" in list(policy.get("violations") or [])
    assert "feedback_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])


def test_build_feedback_adaptation_bundle_baseline():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._build_feedback_adaptation_bundle(
        feedback_bundle={
            "latest_signal": "approve",
            "signals": ["approve"],
            "reason_codes": ["feedback_capture_adapter_normalized"],
        },
        intent_bundle={"intent": "start_project"},
        plan_bundle={"intent": "start_project", "steps": []},
        assistant_mode_enabled=True,
    )
    assert out.get("contract_version") == "v1"
    assert out.get("mode") == "feedback_to_planning_adaptation"
    assert out.get("status") == "ready"
    assert out.get("source") == "deterministic"
    assert out.get("latest_signal") == "approve"
    assert out.get("boosted_intents") == ["start_project"]
    assert out.get("suppressed_intents") == []
    assert "feedback_adaptation_signal_to_plan_ranked" in list(out.get("reason_codes") or [])


def test_build_feedback_adaptation_bundle_ranks_cancel_signal():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._build_feedback_adaptation_bundle(
        feedback_bundle={
            "latest_signal": "cancel",
            "signals": ["cancel"],
            "reason_codes": ["feedback_capture_adapter_normalized"],
        },
        intent_bundle={"intent": "start_project"},
        plan_bundle={"intent": "start_project", "steps": []},
        assistant_mode_enabled=True,
    )
    assert out.get("latest_signal") == "cancel"
    assert out.get("boosted_intents") == ["general_query"]
    assert out.get("suppressed_intents") == ["start_project"]
    assert "feedback_adaptation_signal_to_plan_ranked" in list(out.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_adaptation_policy_forces_fallback_on_violation(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    def _invalid_adaptation_bundle(**kwargs):
        _ = kwargs
        return {
            "contract_version": "v1",
            "mode": "feedback_to_planning_adaptation",
            "status": "ready",
            "source": "deterministic",
            "latest_signal": "unknown",
            "boosted_intents": ["start_project", "prepare_meeting", "general_query"],
            "suppressed_intents": ["start_project", "general_query"],
            "reason_codes": ["feedback_adaptation_signal_to_plan_ranked"],
        }

    monkeypatch.setattr("src.services.answer.answer_service._build_feedback_adaptation_bundle", _invalid_adaptation_bundle)

    http = _DummyHTTP(request_id="rid-adaptation-policy", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="adaptation policy test", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    adaptation = dict(diag.get("assistant_feedback_adaptation") or {})
    policy = dict(diag.get("adaptation_policy") or {})

    assert adaptation.get("latest_signal") == "none"
    assert adaptation.get("boosted_intents") == ["start_project", "prepare_meeting"]
    assert adaptation.get("suppressed_intents") == []
    assert "feedback_adaptation_policy_forced_fallback" in list(adaptation.get("reason_codes") or [])
    assert "feedback_adaptation_latest_signal_not_allowlisted" in list(policy.get("violations") or [])
    assert "feedback_adaptation_boosted_intents_exceed_max" in list(policy.get("violations") or [])
    assert "feedback_adaptation_suppressed_intents_exceed_max" in list(policy.get("violations") or [])
    assert "feedback_adaptation_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_llm_planner_policy_forces_fallback_on_violation(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = True
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = False
        llm_provider = "openai"
        openai_model = "gpt-4o-mini"
        ollama_model = ""

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    async def _fake_planner_with_violation(
        *,
        query,
        intent_payload,
        assistant_mode_enabled,
        llm,
        llm_enabled,
        llm_model,
        llm_error,
    ):
        return (
            {"intent": "general_query", "source": "heuristic", "reason_codes": ["fallback_general_query"]},
            {
                "contract_version": "v1",
                "plan_id": "plan:unknown_intent:abc123",
                "status": "ready",
                "deterministic": True,
                "intent": "unknown_intent",
                "steps": [],
                "requires_confirmation": False,
                "reason_codes": ["deterministic_plan_built"],
            },
            {
                "contract_version": "v1",
                "source": "llm",
                "status": "ready",
                "model": "gpt-4o-mini",
                "intent": "unknown_intent",
                "plan_id": "plan:unknown_intent:abc123",
                "reason_codes": ["llm_planner_adapter_selected_intent"],
            },
        )

    monkeypatch.setattr("src.services.answer.answer_service._build_planner_with_fallback", _fake_planner_with_violation)

    http = _DummyHTTP(request_id="rid-plan-policy-fallback", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="unknown intent policy test", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    planner = dict(diag.get("assistant_llm_planner") or {})
    policy = dict(diag.get("llm_planner_policy") or {})

    assert planner.get("source") == "fallback"
    assert planner.get("status") == "fallback"
    assert "llm_planner_policy_forced_fallback" in list(planner.get("reason_codes") or [])
    assert "llm_planner_intent_not_allowlisted" in list(policy.get("violations") or [])
    assert "llm_planner_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_bridges_plan_to_draft_actions_when_proactive_off(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-plan-bridge", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="new project planning", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    ant = dict(diag.get("anticipatory") or {})
    actions = dict(ant.get("draft_actions") or {})
    rows = list(actions.get("actions") or [])
    assert actions.get("status") == "ready"
    assert actions.get("requires_confirmation") is True
    assert len(rows) >= 1
    assert str((rows[0] or {}).get("action_id", "")).startswith("draft_action:plan:start_project:")
    assert "draft_actions_from_plan_bridge" in list(actions.get("reason_codes") or [])
    handshake = dict(diag.get("assistant_execution_handshake") or {})
    assert handshake.get("state") == "pending_confirmation"
    assert handshake.get("requires_confirmation") is True
    assert str(handshake.get("confirmation_token", "")).startswith("confirm:")
    assert "awaiting_user_confirmation" in list(handshake.get("reason_codes") or [])
    receipt = dict(diag.get("assistant_execution_receipt") or {})
    assert receipt.get("status") == "awaiting_confirmation"
    assert receipt.get("handshake_state") == "pending_confirmation"
    approval = dict(diag.get("assistant_approval_session") or {})
    assert approval.get("status") == "open"
    assert approval.get("requires_confirmation") is True
    assert str(approval.get("approval_id", "")).startswith("approval:")


@pytest.mark.asyncio
async def test_answer_service_planning_policy_blocks_unsafe_steps(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    def _unsafe_plan(**kwargs):
        return {
            "contract_version": "v1",
            "plan_id": "plan:test:unsafe",
            "status": "ready",
            "deterministic": True,
            "intent": "start_project",
            "steps": [
                {
                    "step_id": "step:1",
                    "role": "ops",
                    "action": "execute_shell_command",
                    "parameters": {},
                    "depends_on": [],
                }
            ],
            "requires_confirmation": True,
            "reason_codes": ["deterministic_plan_built"],
        }

    monkeypatch.setattr("src.services.answer.answer_service._build_deterministic_plan", _unsafe_plan)

    http = _DummyHTTP(request_id="rid-plan-guard", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="project", session_id="default")
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    plan = dict(diag.get("assistant_plan") or {})
    policy = dict(diag.get("planning_policy") or {})

    assert plan.get("status") == "guarded"
    assert plan.get("steps") == []
    assert plan.get("requires_confirmation") is False
    assert policy.get("blocked_steps_count") == 1
    assert "unsafe_steps_blocked" in list(policy.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_handshake_transition_approve(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    import src.services.answer.answer_service as answer_service_module

    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()

    http = _DummyHTTP(request_id="rid-handshake-approve", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base_req = AnswerRequest(query="new project planning", session_id="default")
    base_resp = await AnswerService().handle(http, base_req, workspace_id="default")
    base_diag = dict(getattr(base_resp, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")
    ant = dict(base_diag.get("anticipatory") or {})
    draft_actions = dict(ant.get("draft_actions") or {})
    first_action = dict((list(draft_actions.get("actions") or [{}])[0]) or {})
    action_id = str(first_action.get("action_id", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "approve",
            "handshake_confirmation_token": token,
            "handshake_action_ids": [action_id],
            "handshake_idempotency_key": f"idem-approve-{str(token)[-6:]}",
        },
    )
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})

    assert handshake.get("state") == "approved"
    assert handshake.get("requires_confirmation") is False
    assert handshake.get("approved_action_ids") == [action_id]
    assert "user_approved" in list(handshake.get("reason_codes") or [])
    idempotency = dict(diag.get("execution_idempotency") or {})
    assert idempotency.get("status") == "fresh"
    assert str(idempotency.get("idempotency_key", "")).startswith("idem-approve-")
    receipt = dict(diag.get("assistant_execution_receipt") or {})
    assert receipt.get("status") == "recorded"
    assert receipt.get("handshake_state") == "approved"
    assert str(receipt.get("receipt_id", "")).startswith("receipt:")
    assert receipt.get("executed_action_ids") == [action_id]
    gateway = dict(diag.get("assistant_execution_gateway") or {})
    assert gateway.get("state") == "executed_in_pilot"
    assert gateway.get("safe_mode") is True
    assert gateway.get("executed_action_ids") == [action_id]
    assert gateway.get("dry_run_action_ids") == []


@pytest.mark.asyncio
async def test_answer_service_handshake_transition_policy_blocks_unknown_action_ids(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-handshake-policy-unknown", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base_req = AnswerRequest(query="new project planning", session_id="default")
    base_resp = await AnswerService().handle(http, base_req, workspace_id="default")
    base_diag = dict(getattr(base_resp, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "approve",
            "handshake_confirmation_token": token,
            "handshake_action_ids": ["draft_action:unknown"],
            "handshake_idempotency_key": "idem-unknown-1",
        },
    )
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    transition_policy = dict(diag.get("execution_transition_policy") or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})

    assert "unknown_action_ids_blocked" in list(transition_policy.get("applied_reason_codes") or [])
    assert handshake.get("state") == "pending_confirmation"
    assert "no_matching_action_ids" in list(handshake.get("reason_codes") or [])


def test_handshake_transition_policy_blocks_non_allowlisted_action_types():
    import src.services.answer.answer_service as answer_service_module

    policy = answer_service_module._build_transition_policy_contract()
    normalized, eval_bundle = answer_service_module._apply_handshake_transition_policy(
        transition_input={
            "decision": "approve",
            "requested_action_ids": ["draft_action:safe", "draft_action:risky"],
        },
        draft_actions_bundle={
            "actions": [
                {"action_id": "draft_action:safe", "action_type": "prepare_summary_draft"},
                {"action_id": "draft_action:risky", "action_type": "send_email_draft"},
            ]
        },
        policy_contract=policy,
    )

    assert normalized.get("requested_action_ids") == ["draft_action:safe"]
    assert eval_bundle.get("blocked_non_allowlisted_action_ids") == ["draft_action:risky"]
    assert "non_allowlisted_action_types_blocked" in list(eval_bundle.get("applied_reason_codes") or [])


def test_wire_planner_runtime_diagnostics_syncs_plan_id():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._wire_planner_runtime_diagnostics(
        diagnostics={
            "assistant_intent": {"intent": "start_project"},
            "assistant_plan": {"plan_id": "plan:start_project:abc", "intent": "start_project"},
            "assistant_llm_planner": {
                "contract_version": "v1",
                "source": "llm",
                "status": "ready",
                "model": "gpt-4o-mini",
                "intent": "start_project",
                "plan_id": "plan:start_project:old",
                "reason_codes": ["llm_planner_adapter_selected_intent"],
            },
            "llm_planner_policy": {
                "mode": "llm_planner_guarded",
                "allow_llm_source": True,
                "allowed_intents": ["start_project"],
                "require_plan_id_prefix_match": True,
                "fallback_on_policy_violation": True,
                "violations": [],
                "applied_reason_codes": [],
            },
        }
    )

    planner = dict(out.get("assistant_llm_planner") or {})
    policy = dict(out.get("llm_planner_policy") or {})
    assert planner.get("plan_id") == "plan:start_project:abc"
    assert "llm_planner_runtime_plan_id_synced" in list(planner.get("reason_codes") or [])
    assert "llm_planner_runtime_wired" in list(policy.get("applied_reason_codes") or [])


def test_build_answer_service_runtime_context_normalizes_flags():
    import src.services.answer.answer_service as answer_service_module

    class _S:
        feature_reasoning = 1
        feature_graphrag = "yes"
        feature_assistant_mode = True
        feature_assistant_proactive = 0
        feature_assistant_actions = None

    out = answer_service_module._build_answer_service_runtime_context(settings=_S())
    assert out == {
        "reasoning_enabled": True,
        "graphrag_enabled": True,
        "assistant_mode_enabled": True,
        "assistant_proactive_enabled": False,
        "assistant_actions_enabled": False,
        "assistant_response_language": "auto",
    }


def test_build_reasoning_runtime_adapter_requires_synthesize():
    import src.services.answer.answer_service as answer_service_module

    class _Bad:
        pass

    class _Good:
        async def synthesize(self, req):
            _ = req
            return _FakeResp()

    out_bad = answer_service_module._build_reasoning_runtime_adapter(
        reasoning_factory=lambda **kwargs: _Bad(),
        retriever=object(),
        llm=None,
    )
    out_good = answer_service_module._build_reasoning_runtime_adapter(
        reasoning_factory=lambda **kwargs: _Good(),
        retriever=object(),
        llm=None,
    )
    out_none = answer_service_module._build_reasoning_runtime_adapter(
        reasoning_factory=lambda **kwargs: None,
        retriever=object(),
        llm=None,
    )

    assert out_bad is None
    assert out_none is None
    assert out_good is not None


def test_build_memory_consistency_bundle_warns_when_memory_not_loaded():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._build_memory_consistency_bundle(
        session_memory_loaded=False,
        session_memory_hit=False,
        durable_approval_record_loaded=True,
        durable_idempotency_record_loaded=False,
    )
    assert out.get("contract_version") == "v1"
    assert out.get("mode") == "memory_consistency_guarded"
    assert out.get("status") == "warn"
    inputs = dict(out.get("inputs") or {})
    assert inputs == {
        "session_memory_loaded": False,
        "session_memory_hit": False,
        "durable_approval_record_loaded": True,
        "durable_idempotency_record_loaded": False,
    }
    reason_codes = list(out.get("reason_codes") or [])
    assert "memory_consistency_guard_evaluated" in reason_codes
    assert "memory_consistency_store_unavailable" in reason_codes
    assert "memory_consistency_durable_approval_loaded" in reason_codes


def test_build_memory_consistency_strategy_contract_defaults():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._build_memory_consistency_strategy_contract()
    assert out.get("contract_version") == "v1"
    assert out.get("mode") == "best_effort_dual_store"
    assert out.get("consistency_target") == "eventual_consistency"
    assert out.get("write_strategy") == "sqlite_primary_qdrant_best_effort"
    assert out.get("outbox_strategy") == "deferred"
    assert out.get("compensation_strategy") == "deferred"
    reason_codes = list(out.get("reason_codes") or [])
    assert "memory_consistency_strategy_contract_defined" in reason_codes
    assert "memory_consistency_strategy_best_effort" in reason_codes


def test_wire_tool_selection_runtime_diagnostics_syncs_plan_steps():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._wire_tool_selection_runtime_diagnostics(
        diagnostics={
            "assistant_plan": {
                "plan_id": "plan:start_project:abc",
                "intent": "start_project",
                "steps": [
                    {"step_id": "step:1", "action": "prepare_project_workspace_draft"},
                    {"step_id": "step:2", "action": "prepare_project_brief_draft"},
                ],
            },
            "assistant_tool_selection": {
                "contract_version": "v1",
                "mode": "mcp_aware_selector",
                "status": "ready",
                "source": "mcp",
                "selected_tools": [
                    {
                        "step_id": "step:1",
                        "tool_name": "workspace_manager",
                        "route": "mcp_registry_match",
                        "reason": "tool_selection_mcp_match",
                    },
                    {
                        "step_id": "step:orphan",
                        "tool_name": "unknown",
                        "route": "mcp_registry_match",
                        "reason": "orphan",
                    },
                ],
                "blocked_step_ids": [],
                "reason_codes": ["tool_selection_adapter_applied"],
            },
            "tool_selection_policy": {
                "mode": "tool_selection_guarded",
                "allow_mcp_source": True,
                "allow_deterministic_fallback": True,
                "allowed_routes": ["mcp_registry_match", "deterministic_fallback", "diagnostics_only"],
                "require_plan_step_binding": True,
                "max_selected_tools": 5,
                "fallback_on_policy_violation": True,
                "violations": [],
                "applied_reason_codes": [],
            },
        }
    )

    selection = dict(out.get("assistant_tool_selection") or {})
    policy = dict(out.get("tool_selection_policy") or {})
    selected = list(selection.get("selected_tools") or [])
    assert [str((row or {}).get("step_id", "")) for row in selected] == ["step:1", "step:2"]
    assert str((selected[1] or {}).get("route", "")) == "deterministic_fallback"
    assert "step:orphan" in list(selection.get("blocked_step_ids") or [])
    assert "tool_selection_runtime_wired" in list(selection.get("reason_codes") or [])
    assert "tool_selection_runtime_wired" in list(policy.get("applied_reason_codes") or [])
    assert "tool_selection_runtime_orphaned_step_removed" in list(policy.get("violations") or [])


def test_wire_feedback_runtime_diagnostics_normalizes_signals():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._wire_feedback_runtime_diagnostics(
        diagnostics={
            "assistant_feedback_learning": {
                "contract_version": "v1",
                "mode": "approve_cancel_edit_feedback",
                "status": "ready",
                "signals": ["approve", "unknown", "approve"],
                "latest_signal": "edit",
                "signal_counts": {"approve": 0, "cancel": 0, "edit": 0},
                "reason_codes": ["feedback_capture_adapter_normalized"],
            },
            "feedback_policy": {
                "mode": "feedback_learning_guarded",
                "allowed_signals": ["approve", "cancel", "edit"],
                "max_signals_per_request": 3,
                "require_latest_in_signals": True,
                "fallback_on_policy_violation": True,
                "violations": [],
                "applied_reason_codes": [],
            },
        }
    )

    feedback = dict(out.get("assistant_feedback_learning") or {})
    policy = dict(out.get("feedback_policy") or {})
    assert feedback.get("signals") == ["approve", "edit"]
    assert feedback.get("latest_signal") == "edit"
    assert feedback.get("signal_counts") == {"approve": 1, "cancel": 0, "edit": 1}
    assert "feedback_runtime_unknown_signals_removed" in list(feedback.get("reason_codes") or [])
    assert "feedback_runtime_wired" in list(feedback.get("reason_codes") or [])
    assert "feedback_runtime_wired" in list(policy.get("applied_reason_codes") or [])


def test_wire_feedback_adaptation_runtime_diagnostics_syncs_feedback_and_plan():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._wire_feedback_adaptation_runtime_diagnostics(
        diagnostics={
            "assistant_plan": {"intent": "start_project"},
            "assistant_feedback_learning": {
                "latest_signal": "edit",
                "signals": ["edit"],
            },
            "assistant_feedback_adaptation": {
                "contract_version": "v1",
                "mode": "feedback_to_planning_adaptation",
                "status": "ready",
                "source": "deterministic",
                "latest_signal": "approve",
                "boosted_intents": [],
                "suppressed_intents": ["start_project", "unknown_intent"],
                "reason_codes": ["feedback_adaptation_signal_to_plan_ranked"],
            },
            "adaptation_policy": {
                "mode": "feedback_adaptation_guarded",
                "allowed_latest_signals": ["none", "approve", "cancel", "edit"],
                "allowed_intents": ["start_project", "prepare_meeting", "general_query"],
                "max_boosted_intents": 2,
                "max_suppressed_intents": 1,
                "forbid_boost_suppress_overlap": True,
                "fallback_on_policy_violation": True,
                "violations": [],
                "applied_reason_codes": [],
            },
        }
    )

    adaptation = dict(out.get("assistant_feedback_adaptation") or {})
    policy = dict(out.get("adaptation_policy") or {})
    assert adaptation.get("latest_signal") == "edit"
    assert adaptation.get("boosted_intents") == ["start_project"]
    assert adaptation.get("suppressed_intents") == []
    assert "feedback_adaptation_runtime_wired" in list(adaptation.get("reason_codes") or [])
    assert "feedback_adaptation_runtime_backfilled" in list(adaptation.get("reason_codes") or [])
    assert "feedback_adaptation_runtime_wired" in list(policy.get("applied_reason_codes") or [])
    assert "feedback_adaptation_runtime_unknown_intent_removed" in list(policy.get("violations") or [])


def test_wire_assistant_recovery_runtime_diagnostics_normalizes_policy():
    import src.services.answer.answer_service as answer_service_module

    out = answer_service_module._wire_assistant_recovery_runtime_diagnostics(
        diagnostics={
            "response_language": "AUTO",
            "query": "Привет",
            "assistant_chat_recovery_applied": True,
            "planning_reason_codes": ["deterministic_plan_built"],
            "assistant_recovery_policy": {
                "mode": "assistant_chat_recovery_guarded",
                "allow_low_evidence_only": True,
                "allowed_intents": ["general_chat", "unknown"],
                "block_greeting_queries": True,
                "allowed_languages": ["ru", "es"],
                "require_assistant_mode": True,
                "fallback_on_policy_violation": True,
                "target_language": "auto",
                "violations": ["assistant_chat_recovery_greeting_blocked", "unknown_violation"],
                "applied_reason_codes": [],
            },
        }
    )

    policy = dict(out.get("assistant_recovery_policy") or {})
    assert policy.get("target_language") == "ru"
    assert policy.get("allowed_intents") == ["general_chat"]
    assert policy.get("allowed_languages") == ["ru"]
    assert policy.get("violations") == ["assistant_chat_recovery_greeting_blocked"]
    assert "assistant_chat_recovery_policy_forced_fallback" in list(policy.get("applied_reason_codes") or [])
    assert "assistant_chat_recovery_runtime_unknown_violation_removed" in list(policy.get("applied_reason_codes") or [])
    assert "assistant_chat_recovery_runtime_applied_flag_reset" in list(policy.get("applied_reason_codes") or [])
    assert out.get("assistant_chat_recovery_applied") is False


@pytest.mark.asyncio
async def test_answer_service_blocks_approval_when_rollback_plan_missing(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    def _bridge_with_missing_rollback(*, plan_bundle, draft_actions_bundle, language, actions_enabled):
        return {
            "status": "ready",
            "actions": [
                {
                    "action_id": "draft_action:plan:missing_rollback",
                    "action_type": "prepare_summary_draft",
                    "status": "draft",
                    "requires_confirmation": True,
                    "estimated_impact": "low",
                    "parameters": {},
                    "preview": {"title": "x", "summary": "x", "rank": 1},
                    "rollback_plan": "",
                }
            ],
            "top_action_id": "draft_action:plan:missing_rollback",
            "requires_confirmation": True,
            "reason_codes": ["draft_actions_from_plan_bridge"],
            "warnings": [],
        }

    monkeypatch.setattr("src.services.answer.answer_service._bridge_plan_to_draft_actions", _bridge_with_missing_rollback)

    import src.services.answer.answer_service as answer_service_module

    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()

    http = _DummyHTTP(request_id="rid-rollback-missing", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base = await AnswerService().handle(http, AnswerRequest(query="new project planning", session_id="default"), workspace_id="default")
    base_diag = dict(getattr(base, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "approve",
            "handshake_confirmation_token": token,
            "handshake_action_ids": ["draft_action:plan:missing_rollback"],
            "handshake_idempotency_key": "idem-rollback-missing-1",
        },
    )
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})
    transition_policy = dict(diag.get("execution_transition_policy") or {})
    receipt = dict(diag.get("assistant_execution_receipt") or {})

    assert handshake.get("state") == "pending_confirmation"
    assert "rollback_contract_missing_for_approved_actions" in list(handshake.get("reason_codes") or [])
    assert transition_policy.get("rollback_contract_status") == "blocked_missing_rollback_plan"
    assert transition_policy.get("rollback_missing_action_ids") == ["draft_action:plan:missing_rollback"]
    assert receipt.get("status") == "awaiting_confirmation"
    assert receipt.get("rollback_status") == "not_applicable"


@pytest.mark.asyncio
async def test_answer_service_handshake_transition_cancel(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )

    http = _DummyHTTP(request_id="rid-handshake-cancel", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base_req = AnswerRequest(query="new project planning", session_id="default")
    base_resp = await AnswerService().handle(http, base_req, workspace_id="default")
    base_diag = dict(getattr(base_resp, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "cancel",
            "handshake_confirmation_token": token,
            "handshake_idempotency_key": "idem-cancel-1",
        },
    )
    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})

    assert handshake.get("state") == "cancelled"
    assert handshake.get("requires_confirmation") is False
    assert isinstance(handshake.get("blocked_action_ids"), list)
    assert "user_cancelled" in list(handshake.get("reason_codes") or [])
    receipt = dict(diag.get("assistant_execution_receipt") or {})
    assert receipt.get("status") == "recorded"
    assert receipt.get("handshake_state") == "cancelled"
    assert str(receipt.get("receipt_id", "")).startswith("receipt:")
    gateway = dict(diag.get("assistant_execution_gateway") or {})
    assert gateway.get("state") == "cancelled"
    assert gateway.get("executed_action_ids") == []


@pytest.mark.asyncio
async def test_answer_service_idempotency_replay_detected(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    import src.services.answer.answer_service as answer_service_module

    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()

    http = _DummyHTTP(request_id="rid-idem-replay", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base = await AnswerService().handle(http, AnswerRequest(query="new project planning", session_id="default"), workspace_id="default")
    base_diag = dict(getattr(base, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")
    ant = dict(base_diag.get("anticipatory") or {})
    draft_actions = dict(ant.get("draft_actions") or {})
    action_id = str((dict((list(draft_actions.get("actions") or [{}])[0]) or {})).get("action_id", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "approve",
            "handshake_confirmation_token": token,
            "handshake_action_ids": [action_id],
            "handshake_idempotency_key": "idem-replay-1",
        },
    )
    first = await AnswerService().handle(http, req, workspace_id="default")
    first_diag = dict(getattr(first, "diagnostics", {}) or {})
    assert dict(first_diag.get("execution_idempotency") or {}).get("status") == "fresh"

    second = await AnswerService().handle(http, req, workspace_id="default")
    second_diag = dict(getattr(second, "diagnostics", {}) or {})
    idem2 = dict(second_diag.get("execution_idempotency") or {})
    assert idem2.get("status") == "replayed"
    assert "idempotency_replay_detected" in list(idem2.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_persists_durable_records_to_memory_store(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    class _Mem:
        def __init__(self):
            self.data = {}

        async def put(self, *, workspace_id, key, value, metadata=None):
            self.data[(workspace_id, key)] = str(value or "")

        async def get(self, *, workspace_id, key):
            return self.data.get((workspace_id, key))

        async def query(self, *, workspace_id, text, limit=10):
            return []

        async def semantic_query(self, *, workspace_id, text, limit=10):
            return []

    mem = _Mem()
    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: mem)

    http = _DummyHTTP(request_id="rid-durable-store", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="new project planning", session_id="default")
    await AnswerService().handle(http, req, workspace_id="default")

    approval_key = "session:default:durable:approval_session_record"
    idem_last_key = "session:default:durable:idempotency_record:last"
    approval_raw = str(mem.data.get(("default", approval_key), "") or "")
    idem_raw = str(mem.data.get(("default", idem_last_key), "") or "")
    assert approval_raw
    assert idem_raw
    approval = dict(json.loads(approval_raw) or {})
    idem = dict(json.loads(idem_raw) or {})
    assert approval.get("contract_version") == "v1"
    assert idem.get("contract_version") == "v1"


@pytest.mark.asyncio
async def test_answer_service_blocks_consumed_confirmation_token(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    class _Mem:
        def __init__(self):
            self.data = {}

        async def put(self, *, workspace_id, key, value, metadata=None):
            self.data[(workspace_id, key)] = str(value or "")

        async def get(self, *, workspace_id, key):
            return self.data.get((workspace_id, key))

        async def query(self, *, workspace_id, text, limit=10):
            return []

        async def semantic_query(self, *, workspace_id, text, limit=10):
            return []

    mem = _Mem()
    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: mem)
    import src.services.answer.answer_service as answer_service_module

    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()
    http = _DummyHTTP(request_id="rid-consumed-token", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base = await AnswerService().handle(http, AnswerRequest(query="new project planning", session_id="default"), workspace_id="default")
    base_diag = dict(getattr(base, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")
    ant = dict(base_diag.get("anticipatory") or {})
    action_id = str((dict((list((dict(ant.get("draft_actions") or {})).get("actions") or [{}])[0]) or {})).get("action_id", "") or "")

    first = await AnswerService().handle(
        http,
        AnswerRequest(
            query="new project planning",
            session_id="default",
            filters={
                "handshake_decision": "approve",
                "handshake_confirmation_token": token,
                "handshake_action_ids": [action_id],
                "handshake_idempotency_key": "idem-consumed-1",
            },
        ),
        workspace_id="default",
    )
    first_diag = dict(getattr(first, "diagnostics", {}) or {})
    assert dict(first_diag.get("assistant_execution_handshake") or {}).get("state") == "approved"
    approval_key = ("default", "session:default:durable:approval_session_record")
    raw = str(mem.data.get(approval_key, "") or "")
    loaded = dict(json.loads(raw) or {}) if raw else {}
    loaded["confirmation_token"] = token
    loaded["last_decision"] = "approve"
    loaded["token_expires_at"] = str(9999999999)
    mem.data[approval_key] = json.dumps(loaded, ensure_ascii=True, sort_keys=True)

    second = await AnswerService().handle(
        http,
        AnswerRequest(
            query="new project planning",
            session_id="default",
            filters={
                "handshake_decision": "approve",
                "handshake_confirmation_token": token,
                "handshake_action_ids": [action_id],
                "handshake_idempotency_key": "idem-consumed-2",
            },
        ),
        workspace_id="default",
    )
    second_diag = dict(getattr(second, "diagnostics", {}) or {})
    transition_policy = dict(second_diag.get("execution_transition_policy") or {})
    handshake = dict(second_diag.get("assistant_execution_handshake") or {})
    assert "confirmation_token_consumed" in list(transition_policy.get("applied_reason_codes") or [])
    assert handshake.get("state") == "pending_confirmation"


@pytest.mark.asyncio
async def test_answer_service_blocks_expired_confirmation_token(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    class _Mem:
        def __init__(self):
            self.data = {}

        async def put(self, *, workspace_id, key, value, metadata=None):
            self.data[(workspace_id, key)] = str(value or "")

        async def get(self, *, workspace_id, key):
            return self.data.get((workspace_id, key))

        async def query(self, *, workspace_id, text, limit=10):
            return []

        async def semantic_query(self, *, workspace_id, text, limit=10):
            return []

    mem = _Mem()
    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: mem)
    http = _DummyHTTP(request_id="rid-expired-token", rag_engine=object(), hybrid_retriever=_FakeHybrid())

    base = await AnswerService().handle(http, AnswerRequest(query="new project planning", session_id="default"), workspace_id="default")
    base_diag = dict(getattr(base, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")
    ant = dict(base_diag.get("anticipatory") or {})
    action_id = str((dict((list((dict(ant.get("draft_actions") or {})).get("actions") or [{}])[0]) or {})).get("action_id", "") or "")
    approval_key = ("default", "session:default:durable:approval_session_record")
    raw = str(mem.data.get(approval_key, "") or "")
    loaded = dict(json.loads(raw) or {}) if raw else {}
    loaded["confirmation_token"] = token
    loaded["token_expires_at"] = "1"
    loaded["last_decision"] = ""
    mem.data[approval_key] = json.dumps(loaded, ensure_ascii=True, sort_keys=True)

    resp = await AnswerService().handle(
        http,
        AnswerRequest(
            query="new project planning",
            session_id="default",
            filters={
                "handshake_decision": "approve",
                "handshake_confirmation_token": token,
                "handshake_action_ids": [action_id],
                "handshake_idempotency_key": "idem-expired-1",
            },
        ),
        workspace_id="default",
    )
    diag = dict(getattr(resp, "diagnostics", {}) or {})
    transition_policy = dict(diag.get("execution_transition_policy") or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})
    assert "confirmation_token_expired" in list(transition_policy.get("applied_reason_codes") or [])
    assert handshake.get("state") == "pending_confirmation"


@pytest.mark.asyncio
async def test_answer_service_recovers_replay_from_durable_idempotency_record(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_assistant_mode = True
        feature_assistant_proactive = False
        feature_assistant_actions = True
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    class _Mem:
        def __init__(self):
            self.data = {}

        async def put(self, *, workspace_id, key, value, metadata=None):
            self.data[(workspace_id, key)] = str(value or "")

        async def get(self, *, workspace_id, key):
            return self.data.get((workspace_id, key))

        async def query(self, *, workspace_id, text, limit=10):
            return []

        async def semantic_query(self, *, workspace_id, text, limit=10):
            return []

    mem = _Mem()
    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)
    monkeypatch.setattr(
        "src.core.providers.get_reasoning_engine",
        lambda *, retriever=None, llm=None, llm_timeout_s=None: _FakeReasoningEngine(retriever),
    )
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: mem)
    import src.services.answer.answer_service as answer_service_module

    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()
    http = _DummyHTTP(request_id="rid-durable-replay", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    base = await AnswerService().handle(http, AnswerRequest(query="new project planning", session_id="default"), workspace_id="default")
    base_diag = dict(getattr(base, "diagnostics", {}) or {})
    token = str((dict(base_diag.get("assistant_execution_handshake") or {})).get("confirmation_token", "") or "")
    ant = dict(base_diag.get("anticipatory") or {})
    action_id = str((dict((list((dict(ant.get("draft_actions") or {})).get("actions") or [{}])[0]) or {})).get("action_id", "") or "")

    req = AnswerRequest(
        query="new project planning",
        session_id="default",
        filters={
            "handshake_decision": "approve",
            "handshake_confirmation_token": token,
            "handshake_action_ids": [action_id],
            "handshake_idempotency_key": "idem-durable-replay-1",
        },
    )
    first = await AnswerService().handle(http, req, workspace_id="default")
    first_diag = dict(getattr(first, "diagnostics", {}) or {})
    assert dict(first_diag.get("execution_idempotency") or {}).get("status") == "fresh"

    # Simulate restart: clear in-memory idempotency index, keep durable store intact.
    answer_service_module._EXECUTION_IDEMPOTENCY_SEEN.clear()

    second = await AnswerService().handle(http, req, workspace_id="default")
    second_diag = dict(getattr(second, "diagnostics", {}) or {})
    idem2 = dict(second_diag.get("execution_idempotency") or {})
    assert idem2.get("status") == "replayed"
    assert "idempotency_replay_recovered_from_durable" in list(idem2.get("reason_codes") or [])
