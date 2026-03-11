from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService
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
