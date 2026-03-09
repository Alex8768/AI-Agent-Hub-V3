from __future__ import annotations

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
        "reasoning_trace",
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
