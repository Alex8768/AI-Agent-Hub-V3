from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine
from src.layers.pro.reasoning.graph.state import AgentState


class _FakeRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [
                {"type": "chunk", "id": "c1", "source_refs": ["doc:R#1"], "confidence": 0.5},
            ],
        }


class _FakeLLM:
    async def generate(self, prompt: str) -> str:
        return "LLM_FALLBACK_ANSWER"


def _final_state_from(initial: AgentState) -> dict[str, object]:
    return {
        "query": initial.query,
        "workspace_id": initial.workspace_id,
        "session_id": initial.session_id,
        "session_memory_last_answer": initial.session_memory_last_answer,
        "k": initial.k,
        "graph_depth": initial.graph_depth,
        "max_context_chars": initial.max_context_chars,
        "messages": [],
        "plan": ["SEARCH", "ANSWER"],
        "current_action": "ANSWER",
        "current_step": 1,
        "provenance": [{"type": "chunk", "id": "c1", "source_refs": ["doc:R#1"], "origin": "vector"}],
        "used_chunks": ["c1"],
        "used_nodes": [],
        "used_edges": [],
        "context_preview": "doc:R#1",
        "final_answer": "PLANNER_ANSWER",
        "error": None,
        "iteration_count": 1,
        "max_iterations": 10,
    }


@pytest.mark.asyncio
async def test_planner_runtime_uses_compile_and_ainvoke(monkeypatch):
    calls: dict[str, int] = {"compile": 0, "ainvoke": 0}

    class _Compiled:
        async def ainvoke(self, initial: AgentState):
            calls["ainvoke"] += 1
            return _final_state_from(initial)

    class _Graph:
        def compile(self):
            calls["compile"] += 1
            return _Compiled()

    monkeypatch.setattr("src.layers.pro.reasoning.engine.build_reasoning_graph", lambda llm, retr: _Graph())

    eng = ReasoningEngine(retriever=_FakeRetriever(), llm=_FakeLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert resp.answer == "PLANNER_ANSWER"
    assert calls["compile"] == 1
    assert calls["ainvoke"] == 1
    assert diag.get("planner_path_used") is True
    assert "fallback_reason" not in diag


@pytest.mark.asyncio
async def test_planner_runtime_uses_compile_and_invoke_when_ainvoke_missing(monkeypatch):
    calls: dict[str, int] = {"compile": 0, "invoke": 0}

    class _Compiled:
        def invoke(self, initial: AgentState):
            calls["invoke"] += 1
            return _final_state_from(initial)

    class _Graph:
        def compile(self):
            calls["compile"] += 1
            return _Compiled()

    monkeypatch.setattr("src.layers.pro.reasoning.engine.build_reasoning_graph", lambda llm, retr: _Graph())

    eng = ReasoningEngine(retriever=_FakeRetriever(), llm=_FakeLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert resp.answer == "PLANNER_ANSWER"
    assert calls["compile"] == 1
    assert calls["invoke"] == 1
    assert diag.get("planner_path_used") is True
    assert "fallback_reason" not in diag


@pytest.mark.asyncio
async def test_planner_runtime_without_invoke_methods_falls_back_with_reason(monkeypatch):
    class _Compiled:
        pass

    class _Graph:
        def compile(self):
            return _Compiled()

    monkeypatch.setattr("src.layers.pro.reasoning.engine.build_reasoning_graph", lambda llm, retr: _Graph())

    eng = ReasoningEngine(retriever=_FakeRetriever(), llm=_FakeLLM())
    resp = await eng.synthesize(AnswerRequest(query="Q?"))
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    assert diag.get("planner_path_used") is False
    assert "fallback_reason" in diag
    assert "does not support invoke/ainvoke" in str(diag.get("fallback_reason") or "")
