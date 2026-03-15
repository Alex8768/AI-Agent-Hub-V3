from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService
from src.services.answer.answer_service import _apply_diagnostics
from src.services.answer.answer_service import _save_session_memory
from src.services.answer.answer_service import log_observability
from src.services.answer.interface_contract import build_answer_service_request_contract
from src.services.answer.orchestrator import run_answer_orchestration_core
from src.services.answer.response_assembly import run_answer_response_assembly


class _RespWithDiagnostics:
    def __init__(self):
        self.answer = "ok"
        self.diagnostics = {"planning_reason_codes": []}
        self.provenance = []
        self.timings = {}
        self._request_id = ""
        self.workspace_id = ""

    @property
    def request_id(self) -> str:
        return self._request_id

    @request_id.setter
    def request_id(self, value: str) -> None:
        _ = value
        raise RuntimeError("request-id-write-failed")


class _ReasoningAdapter:
    async def synthesize(self, req):
        _ = req
        return _RespWithDiagnostics()


class _ReasoningAdapterWithFailingRequestIdFallback:
    async def synthesize(self, req):
        _ = req
        return _RespWithFailingRequestIdFallback()


class _RespWithFailingRequestIdFallback:
    __slots__ = ("answer", "diagnostics", "provenance", "timings", "_request_id")

    def __init__(self):
        self.answer = "ok"
        self.diagnostics = {"planning_reason_codes": []}
        self.provenance = []
        self.timings = {}
        self._request_id = ""

    @property
    def request_id(self) -> str:
        return self._request_id

    @request_id.setter
    def request_id(self, value: str) -> None:
        _ = value
        raise RuntimeError("request-id-write-failed")


class _RetrieverAdapter:
    def __init__(self, *, engine, hybrid, workspace_id):
        self.engine = engine
        self.hybrid = hybrid
        self.workspace_id = workspace_id


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


@pytest.mark.asyncio
async def test_response_assembly_writes_soft_failure_reason_code():
    resp = SimpleNamespace(answer="ok", diagnostics={"planning_reason_codes": []})
    req = SimpleNamespace(query="q")

    async def _recovery(**kwargs):
        _ = kwargs
        return "ok"

    def _raise_parity(**kwargs):
        _ = kwargs
        raise RuntimeError("parity-build-failed")

    out = await run_answer_response_assembly(
        resp=resp,
        req=req,
        llm=None,
        assistant_mode_enabled=True,
        assistant_response_language="en",
        build_assistant_recovery_policy_contract=lambda: {},
        apply_assistant_recovery_policy_guards=lambda **kwargs: (True, {"applied_reason_codes": []}),
        build_assistant_chat_recovery_answer=_recovery,
        normalize_low_evidence_friendliness=lambda **kwargs: str(kwargs.get("answer", "") or ""),
        build_conversational_runtime_parity_bundle=_raise_parity,
        build_truthfulness_guard_bundle=lambda **kwargs: {"status": "ok", "reason_codes": ["truthfulness_guard_evaluated"]},
    )

    diag = dict(getattr(out, "diagnostics", None) or {})
    assert "answer_response_assembly_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_orchestrator_writes_soft_failure_reason_code_for_request_id_assignment():
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})
    req = SimpleNamespace(query="q", session_id="s1")

    async def _build_llm_adapter(*, settings):
        _ = settings
        return None, False, "", "", ""

    async def _load_session_memory(**kwargs):
        _ = kwargs
        return False, False

    async def _load_durable_records(**kwargs):
        _ = kwargs
        return {}, {}

    async def _apply_diagnostics(**kwargs):
        resp = kwargs["resp"]
        resp.diagnostics = {"planning_reason_codes": []}

    out = await run_answer_orchestration_core(
        http=http,
        req=req,
        workspace_id="default",
        settings=SimpleNamespace(),
        engine=object(),
        hybrid=object(),
        runtime_context={
            "assistant_mode_enabled": False,
            "assistant_proactive_enabled": False,
            "assistant_actions_enabled": False,
            "assistant_response_language": "auto",
        },
        get_reasoning_engine=lambda **kwargs: _ReasoningAdapter(),
        get_memory_store=lambda: None,
        build_llm_adapter=_build_llm_adapter,
        load_session_memory=_load_session_memory,
        load_durable_records=_load_durable_records,
        retriever_adapter_cls=_RetrieverAdapter,
        build_reasoning_runtime_adapter=lambda **kwargs: _ReasoningAdapter(),
        detect_response_language=lambda _query: "en",
        build_assistant_fallback_answer=lambda **kwargs: "fallback",
        apply_diagnostics=_apply_diagnostics,
    )

    diag = dict(getattr(out.resp, "diagnostics", None) or {})
    assert "answer_orchestrator_request_id_assignment_failed" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_orchestrator_writes_soft_failure_reason_code_for_request_id_fallback_assignment():
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})
    req = SimpleNamespace(query="q", session_id="s1")

    async def _build_llm_adapter(*, settings):
        _ = settings
        return None, False, "", "", ""

    async def _load_session_memory(**kwargs):
        _ = kwargs
        return False, False

    async def _load_durable_records(**kwargs):
        _ = kwargs
        return {}, {}

    async def _apply_diagnostics(**kwargs):
        resp = kwargs["resp"]
        resp.diagnostics = {"planning_reason_codes": []}

    out = await run_answer_orchestration_core(
        http=http,
        req=req,
        workspace_id="default",
        settings=SimpleNamespace(),
        engine=object(),
        hybrid=object(),
        runtime_context={
            "assistant_mode_enabled": False,
            "assistant_proactive_enabled": False,
            "assistant_actions_enabled": False,
            "assistant_response_language": "auto",
        },
        get_reasoning_engine=lambda **kwargs: None,
        get_memory_store=lambda: None,
        build_llm_adapter=_build_llm_adapter,
        load_session_memory=_load_session_memory,
        load_durable_records=_load_durable_records,
        retriever_adapter_cls=_RetrieverAdapter,
        build_reasoning_runtime_adapter=lambda **kwargs: _ReasoningAdapterWithFailingRequestIdFallback(),
        detect_response_language=lambda _query: "en",
        build_assistant_fallback_answer=lambda **kwargs: "fallback",
        apply_diagnostics=_apply_diagnostics,
    )

    diag = dict(getattr(out.resp, "diagnostics", None) or {})
    reason_codes = list(diag.get("planning_reason_codes") or [])
    assert "answer_orchestrator_request_id_assignment_failed" in reason_codes
    assert "answer_orchestrator_request_id_fallback_assignment_failed" in reason_codes


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_durable_persist(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: None)
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: None)

    async def _fake_orchestration(**kwargs):
        _ = kwargs
        resp = SimpleNamespace(
            answer="ok",
            diagnostics={"planning_reason_codes": []},
            timings={},
            provenance=[],
            used_chunks=[],
            used_nodes=[],
            used_edges=[],
        )
        return SimpleNamespace(
            resp=resp,
            llm=None,
            assistant_mode_enabled=False,
            assistant_proactive_enabled=False,
            assistant_actions_enabled=False,
            assistant_response_language="en",
            loaded_durable_approval={},
            loaded_durable_idempotency={},
        )

    async def _fake_response_assembly(**kwargs):
        return kwargs["resp"]

    async def _raise_persist(**kwargs):
        _ = kwargs
        raise RuntimeError("persist-failed")

    async def _noop_save(**kwargs):
        _ = kwargs
        return None

    monkeypatch.setattr("src.services.answer.answer_service.run_answer_orchestration_core", _fake_orchestration)
    monkeypatch.setattr("src.services.answer.answer_service.run_answer_response_assembly", _fake_response_assembly)
    monkeypatch.setattr("src.services.answer.answer_service._persist_durable_records", _raise_persist)
    monkeypatch.setattr("src.services.answer.answer_service._save_session_memory", _noop_save)

    req = AnswerRequest(query="q", session_id="s1", filters={})
    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=object())
    contract = build_answer_service_request_contract(
        http=http,
        req=req,
        workspace_id="default",
        engine=object(),
        retriever=object(),
    )

    resp = await AnswerService().handle_contract(contract)
    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_durable_persist_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_durable_hydration(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: None)
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: None)

    async def _fake_orchestration(**kwargs):
        _ = kwargs
        resp = SimpleNamespace(
            answer="ok",
            diagnostics={"planning_reason_codes": []},
            timings={},
            provenance=[],
            used_chunks=[],
            used_nodes=[],
            used_edges=[],
        )
        return SimpleNamespace(
            resp=resp,
            llm=None,
            assistant_mode_enabled=False,
            assistant_proactive_enabled=False,
            assistant_actions_enabled=False,
            assistant_response_language="en",
            loaded_durable_approval={},
            loaded_durable_idempotency={},
        )

    async def _fake_response_assembly(**kwargs):
        return kwargs["resp"]

    def _raise_hydration(**kwargs):
        _ = kwargs
        raise RuntimeError("hydrate-failed")

    async def _noop_persist(**kwargs):
        _ = kwargs
        return None

    async def _noop_save(**kwargs):
        _ = kwargs
        return None

    monkeypatch.setattr("src.services.answer.answer_service.run_answer_orchestration_core", _fake_orchestration)
    monkeypatch.setattr("src.services.answer.answer_service.run_answer_response_assembly", _fake_response_assembly)
    monkeypatch.setattr("src.services.answer.answer_service._hydrate_durable_records_into_diagnostics", _raise_hydration)
    monkeypatch.setattr("src.services.answer.answer_service._persist_durable_records", _noop_persist)
    monkeypatch.setattr("src.services.answer.answer_service._save_session_memory", _noop_save)

    req = AnswerRequest(query="q", session_id="s1", filters={})
    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=object())
    contract = build_answer_service_request_contract(
        http=http,
        req=req,
        workspace_id="default",
        engine=object(),
        retriever=object(),
    )

    resp = await AnswerService().handle_contract(contract)
    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_durable_hydration_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_post_orchestration(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: None)
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: None)

    async def _fake_orchestration(**kwargs):
        _ = kwargs
        resp = SimpleNamespace(
            answer="ok",
            diagnostics={"planning_reason_codes": []},
            timings={},
            provenance=[],
            used_chunks=[],
            used_nodes=[],
            used_edges=[],
        )
        return SimpleNamespace(
            resp=resp,
            llm=None,
            assistant_mode_enabled=False,
            assistant_proactive_enabled=False,
            assistant_actions_enabled=False,
            assistant_response_language="en",
            loaded_durable_approval={},
            loaded_durable_idempotency={},
        )

    async def _fake_response_assembly(**kwargs):
        return kwargs["resp"]

    def _raise_runtime_diagnostics(**kwargs):
        _ = kwargs
        raise RuntimeError("runtime-diagnostics-failed")

    async def _noop_persist(**kwargs):
        _ = kwargs
        return None

    async def _noop_save(**kwargs):
        _ = kwargs
        return None

    monkeypatch.setattr("src.services.answer.answer_service.run_answer_orchestration_core", _fake_orchestration)
    monkeypatch.setattr("src.services.answer.answer_service.run_answer_response_assembly", _fake_response_assembly)
    monkeypatch.setattr("src.services.answer.answer_service._wire_runtime_diagnostics", _raise_runtime_diagnostics)
    monkeypatch.setattr("src.services.answer.answer_service._persist_durable_records", _noop_persist)
    monkeypatch.setattr("src.services.answer.answer_service._save_session_memory", _noop_save)

    req = AnswerRequest(query="q", session_id="s1", filters={})
    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=object())
    contract = build_answer_service_request_contract(
        http=http,
        req=req,
        workspace_id="default",
        engine=object(),
        retriever=object(),
    )

    resp = await AnswerService().handle_contract(contract)
    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_post_orchestration_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_apply_diagnostics(monkeypatch):
    def _raise_intent(**kwargs):
        _ = kwargs
        raise RuntimeError("intent-build-failed")

    monkeypatch.setattr("src.services.answer.answer_service._infer_assistant_intent", _raise_intent)

    req = AnswerRequest(query="q", session_id="s1", filters={})
    resp = SimpleNamespace(
        answer="ok",
        diagnostics={"planning_reason_codes": []},
        provenance=[],
        used_chunks=[],
        used_nodes=[],
        used_edges=[],
    )
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})

    await _apply_diagnostics(
        resp=resp,
        req=req,
        http=http,
        workspace_id="default",
        retriever=SimpleNamespace(last_stats={}),
        llm=None,
        llm_enabled=False,
        llm_provider_name="",
        llm_model="",
        llm_error="",
        assistant_mode_enabled=False,
        assistant_proactive_enabled=False,
        assistant_actions_enabled=False,
        assistant_response_language="auto",
        session_memory_loaded=False,
        session_memory_hit=False,
        durable_approval_record_loaded=False,
        durable_idempotency_record_loaded=False,
    )

    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_apply_diagnostics_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_retriever_stats_diagnostics(monkeypatch):
    class _BrokenRetriever:
        @property
        def last_stats(self):
            raise RuntimeError("retriever-stats-read-failed")

    req = AnswerRequest(query="q", session_id="s1", filters={})
    resp = SimpleNamespace(
        answer="ok",
        diagnostics={"planning_reason_codes": []},
        provenance=[],
        used_chunks=[],
        used_nodes=[],
        used_edges=[],
    )
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})

    await _apply_diagnostics(
        resp=resp,
        req=req,
        http=http,
        workspace_id="default",
        retriever=_BrokenRetriever(),
        llm=None,
        llm_enabled=False,
        llm_provider_name="",
        llm_model="",
        llm_error="",
        assistant_mode_enabled=False,
        assistant_proactive_enabled=False,
        assistant_actions_enabled=False,
        assistant_response_language="auto",
        session_memory_loaded=False,
        session_memory_hit=False,
        durable_approval_record_loaded=False,
        durable_idempotency_record_loaded=False,
    )

    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_retriever_stats_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_writes_soft_failure_reason_code_for_evidence_type_counts_diagnostics():
    class _BadEvidenceTypeCounts:
        def __iter__(self):
            raise RuntimeError("evidence-type-counts-bad-iter")

    req = AnswerRequest(query="q", session_id="s1", filters={})
    resp = SimpleNamespace(
        answer="ok",
        diagnostics={"planning_reason_codes": [], "evidence_type_counts": _BadEvidenceTypeCounts()},
        provenance=[],
        used_chunks=[],
        used_nodes=[],
        used_edges=[],
    )
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})

    await _apply_diagnostics(
        resp=resp,
        req=req,
        http=http,
        workspace_id="default",
        retriever=SimpleNamespace(last_stats={}),
        llm=None,
        llm_enabled=False,
        llm_provider_name="",
        llm_model="",
        llm_error="",
        assistant_mode_enabled=False,
        assistant_proactive_enabled=False,
        assistant_actions_enabled=False,
        assistant_response_language="auto",
        session_memory_loaded=False,
        session_memory_hit=True,
        durable_approval_record_loaded=False,
        durable_idempotency_record_loaded=False,
    )

    diag = dict(getattr(resp, "diagnostics", None) or {})
    assert "answer_service_evidence_type_counts_soft_failure" in list(diag.get("planning_reason_codes") or [])


@pytest.mark.asyncio
async def test_answer_service_save_session_memory_does_not_raise_when_failure_diagnostics_fails():
    class _FailingDiagnosticsResp:
        def __init__(self):
            self.answer = "ok"

        @property
        def diagnostics(self):
            raise RuntimeError("diagnostics-read-failed")

        @diagnostics.setter
        def diagnostics(self, value):
            _ = value
            raise RuntimeError("diagnostics-write-failed")

    class _Mem:
        async def put(self, **kwargs):
            _ = kwargs
            raise RuntimeError("memory-put-failed")

    req = AnswerRequest(query="q", session_id="s1", filters={})
    resp = _FailingDiagnosticsResp()

    await _save_session_memory(
        req=req,
        resp=resp,
        workspace_id="default",
        get_memory_store=lambda: _Mem(),
    )


@pytest.mark.asyncio
async def test_answer_service_save_session_memory_sets_failure_flag_when_persist_fails():
    class _Resp:
        def __init__(self):
            self.answer = "ok"
            self.diagnostics = {}

    class _Mem:
        async def put(self, **kwargs):
            _ = kwargs
            raise RuntimeError("memory-put-failed")

    req = AnswerRequest(query="q", session_id="s1", filters={})
    resp = _Resp()

    await _save_session_memory(
        req=req,
        resp=resp,
        workspace_id="default",
        get_memory_store=lambda: _Mem(),
    )

    assert dict(getattr(resp, "diagnostics", None) or {}).get("session_memory_saved") is False


def test_answer_service_log_observability_does_not_raise_when_logger_fails(monkeypatch):
    class _FailingLogger:
        @staticmethod
        def info(*args, **kwargs):
            _ = args, kwargs
            raise RuntimeError("logger-failed")

    monkeypatch.setattr("loguru.logger", _FailingLogger())
    http = SimpleNamespace(state=SimpleNamespace(request_id="rid-soft"), headers={})
    req = AnswerRequest(query="hello", session_id="s1", filters={})
    log_observability(http, workspace_id="default", req=req)
