from __future__ import annotations

from types import SimpleNamespace

import pytest

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
