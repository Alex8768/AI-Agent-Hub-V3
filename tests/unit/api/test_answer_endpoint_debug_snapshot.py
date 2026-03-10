from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings


def test_answer_endpoint_includes_debug_snapshot_when_debug_enabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "debug", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    # Provide required state deps
    app.state.rag_engine = object()

    import types
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    async def _fake_retrieve(self, **kwargs):
        # Provide some evidence that becomes provenance
        return types.SimpleNamespace(
            graph={"nodes": [{"id": "n1"}], "edges": [{"id": "e1"}]},
            evidence=[
                {"type": "chunk", "id": "c1", "source_refs": ["doc1"], "score": 1.0},
                {"type": "memory", "id": "m1", "source_refs": ["mem"], "score": 0.9},
                {"type": "edge", "id": "e1", "source_refs": ["g"], "confidence": 0.5},
            ],
            results=[{"chunk_id": "c1"}],
            stats={"memory_mode": "semantic", "memory_candidates_count": 1, "memory_added_evidence_count": 1},
        )

    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)
    app.state.hybrid_retriever = hr.HybridRetriever()

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {
        "answer",
        "confidence",
        "context_preview",
        "provenance",
        "used_chunks",
        "used_nodes",
        "used_edges",
        "request_id",
        "workspace_id",
        "timings",
        "warnings",
        "diagnostics",
    }

    diag = body.get("diagnostics") or {}
    assert set(diag.keys()) == {
        "agent_current_action",
        "agent_current_step",
        "retrieved_provenance_count",
        "used_chunks_count",
        "used_nodes_count",
        "used_edges_count",
        "planner_path_used",
        "fallback_reason",
        "evidence_summary",
        "has_llm",
        "query_len",
        "k",
        "graph_depth",
        "session_id",
        "evidence_contract",
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
        "session_memory_loaded",
        "session_memory_hit",
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
        "assistant_mode_enabled",
        "assistant_proactive_enabled",
        "assistant_actions_enabled",
        "intent_contract_version",
        "plan_contract_version",
        "assistant_intent",
        "assistant_plan",
        "planning_policy",
        "execution_handshake_contract_version",
        "assistant_execution_handshake",
        "execution_transition_policy",
        "execution_receipt_contract_version",
        "assistant_execution_receipt",
        "approval_session_contract_version",
        "assistant_approval_session",
        "planning_reason_codes",
        "plan_id",
        "retriever_stats",
        "session_memory_saved",
    }
    assert "trace_id" in diag
    assert "evidence_type_counts" in diag
    assert "top_evidence" in diag
    assert isinstance(diag["top_evidence"], list)
    assert any(x.startswith("chunk:") for x in diag["top_evidence"])
    assert diag.get("intent_contract_version") == "v1"
    assert diag.get("plan_contract_version") == "v1"
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
        "allowed_decisions",
        "requested_action_ids_count",
        "available_action_ids_count",
        "unknown_action_ids",
        "applied_reason_codes",
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
    assert isinstance(diag.get("planning_reason_codes"), list)
    assert isinstance(diag.get("plan_id"), str)
    assert diag.get("evidence_contract_version") == "v1"
    assert isinstance(diag.get("evidence_contract_valid_minimal"), bool)
    assert isinstance(diag.get("evidence_contract_missing_minimal_fields"), list)
    assert isinstance(diag.get("evidence_contract_missing_minimal_count"), int)
    assert isinstance(diag.get("evidence_contract_minimal_coverage_score"), float)
    assert isinstance(diag.get("evidence_contract_gate_reason"), str)
    sc = dict(diag.get("self_check") or {})
    assert sc.get("version") == "v1"
    assert sc.get("status") == "pass"
    assert sc.get("reasons") == []
    assert sc.get("policy_mode") == "warning_only"
    sc_inputs = dict(sc.get("inputs") or {})
    assert set(sc_inputs.keys()) == {
        "evidence_contract_valid_minimal",
        "evidence_contract_missing_minimal_count",
        "evidence_contract_minimal_coverage_score",
    }
    assert sc_inputs.get("evidence_contract_valid_minimal") is True
    assert sc_inputs.get("evidence_contract_missing_minimal_count") == 0
    assert sc_inputs.get("evidence_contract_minimal_coverage_score") == 1.0
    sc_thresholds = dict(sc.get("thresholds") or {})
    assert sc_thresholds.get("minimal_coverage_score_min") == 1.0
    assert sc_thresholds.get("missing_minimal_count_max") == 0
    verify = dict(diag.get("verify") or {})
    assert verify.get("version") == "v1"
    assert verify.get("status") == "pass"
    assert verify.get("reasons") == []
    assert verify.get("policy_mode") == "warning_only"
    v_inputs = dict(verify.get("inputs") or {})
    assert set(v_inputs.keys()) == {
        "planner_path_used",
        "self_check_status",
        "self_check_policy_mode",
        "self_check_reasons_count",
    }
    assert v_inputs.get("planner_path_used") is False
    assert v_inputs.get("self_check_status") == "pass"
    assert v_inputs.get("self_check_policy_mode") == "warning_only"
    assert v_inputs.get("self_check_reasons_count") == 0
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

    # cleanup
    try:
        delattr(app.state, "hybrid_retriever")
    except Exception:
        pass
    try:
        delattr(app.state, "rag_engine")
    except Exception:
        pass
