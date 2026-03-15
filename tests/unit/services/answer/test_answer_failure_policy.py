from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService
from src.services.answer.interface_contract import build_answer_service_request_contract


class _DummyState:
    request_id = "rid-failure-policy"


class _DummyAppState:
    rag_engine = object()
    hybrid_retriever = object()


class _DummyApp:
    state = _DummyAppState()


class _DummyHTTP:
    state = _DummyState()
    headers = {}
    app = _DummyApp()


@pytest.mark.asyncio
async def test_answer_service_returns_controlled_fallback_on_runtime_failure(monkeypatch) -> None:
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_assistant_mode = False
        feature_assistant_proactive = False
        feature_assistant_actions = False

    async def _boom(**_: object):
        raise RuntimeError("boom")

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.services.answer.answer_service._run_answer_primary_pipeline", _boom)

    service = AnswerService()
    contract = build_answer_service_request_contract(
        http=_DummyHTTP(),
        req=AnswerRequest(query="trigger"),
        workspace_id="default",
        engine=object(),
        retriever=object(),
    )
    resp = await service.handle_contract(contract)
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    failure_policy = dict(diagnostics.get("failure_policy") or {})

    assert "answer_runtime_controlled_fallback" in list(getattr(resp, "warnings", []) or [])
    assert failure_policy.get("mode") == "controlled_fallback"
    assert failure_policy.get("reason_code") == "answer_runtime_controlled_fallback"
