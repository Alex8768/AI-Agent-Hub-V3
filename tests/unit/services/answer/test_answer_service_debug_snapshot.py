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
    gateway = dict(diag.get("assistant_execution_gateway") or {})
    assert gateway.get("state") == "ready_for_execution"
    assert gateway.get("safe_mode") is True
    assert gateway.get("executed_action_ids") == []
    assert gateway.get("dry_run_action_ids") == [action_id]


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
