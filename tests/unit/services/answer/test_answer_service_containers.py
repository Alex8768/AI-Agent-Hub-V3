from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.answer_service import AnswerService


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


class _Resp:
    def __init__(self):
        self.answer = "ok"
        self.diagnostics = {}
        self.timings = {}
        self.provenance = []
        self.used_chunks = []
        self.used_nodes = []
        self.used_edges = []


@pytest.mark.asyncio
async def test_answer_service_routes_dialog_to_dialog_container(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: object())
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: object())

    called = {"dialog": 0, "action": 0}

    async def _fake_dialog_container(**kwargs):
        _ = kwargs
        called["dialog"] += 1
        return _Resp()

    async def _fake_action_container(**kwargs):
        _ = kwargs
        called["action"] += 1
        return _Resp()

    monkeypatch.setattr(
        "src.services.answer.answer_service.run_dialog_container",
        _fake_dialog_container,
    )
    monkeypatch.setattr(
        "src.services.answer.answer_service.run_action_container",
        _fake_action_container,
    )

    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=object())
    req = AnswerRequest(query="Привет, кто ты?", k=4, graph_depth=1, filters={})

    await AnswerService().handle(http, req, workspace_id="default")

    assert called["dialog"] == 1
    assert called["action"] == 0


@pytest.mark.asyncio
async def test_answer_service_routes_action_to_action_container(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: object())
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: object())

    called = {"dialog": 0, "action": 0}

    async def _fake_dialog_container(**kwargs):
        _ = kwargs
        called["dialog"] += 1
        return _Resp()

    async def _fake_action_container(**kwargs):
        _ = kwargs
        called["action"] += 1
        return _Resp()

    monkeypatch.setattr(
        "src.services.answer.answer_service.run_dialog_container",
        _fake_dialog_container,
    )
    monkeypatch.setattr(
        "src.services.answer.answer_service.run_action_container",
        _fake_action_container,
    )

    http = _DummyHTTP(request_id="rid-2", rag_engine=object(), hybrid_retriever=object())
    req = AnswerRequest(query="Выполни команду ls", k=4, graph_depth=1, filters={})

    await AnswerService().handle(http, req, workspace_id="default")

    assert called["dialog"] == 0
    assert called["action"] == 1


@pytest.mark.asyncio
async def test_answer_service_canary_override_disables_agent_router(monkeypatch):
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        feature_agent_router_v1 = True

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())
    monkeypatch.setattr("src.core.providers.get_reasoning_engine", lambda **kwargs: object())
    monkeypatch.setattr("src.core.providers.get_memory_store", lambda: object())

    called = {"dialog": 0, "action": 0}

    async def _fake_dialog_container(**kwargs):
        _ = kwargs
        called["dialog"] += 1
        return _Resp()

    async def _fake_action_container(**kwargs):
        _ = kwargs
        called["action"] += 1
        return _Resp()

    monkeypatch.setattr("src.services.answer.answer_service.run_dialog_container", _fake_dialog_container)
    monkeypatch.setattr("src.services.answer.answer_service.run_action_container", _fake_action_container)

    http = _DummyHTTP(request_id="rid-3", rag_engine=object(), hybrid_retriever=object())
    req = AnswerRequest(
        query="Привет, кто ты?",
        k=4,
        graph_depth=1,
        filters={"feature_agent_router_v1": "false"},
    )

    out = await AnswerService().handle(http, req, workspace_id="default")
    assert called["dialog"] == 0
    assert called["action"] == 1
    diag = dict(getattr(out, "diagnostics", {}) or {})
    marker = dict(diag.get("agent_router_v1") or {})
    assert marker.get("enabled") is False

