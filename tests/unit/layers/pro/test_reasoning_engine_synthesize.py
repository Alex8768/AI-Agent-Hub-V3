from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.engine import ReasoningEngine


class _FakeRetriever:
    def __init__(self):
        self.calls = []

    async def retrieve(self, request):
        self.calls.append(request)

        return {
            "results": [{"chunk_id": "chunk:1"}, {"chunk_id": "chunk:2"}],
            "graph": {
                "nodes": [{"id": "node:1"}, {"id": "node:2"}],
                "edges": [{"id": "edge:1"}],
            },
            "evidence": [
                {"type": "chunk", "id": "chunk:1", "source_refs": ["doc:A#1"], "confidence": 0.9},
                # malformed evidence should be ignored
                {"bad": "shape"},
            ],
        }


class _EmptyRetriever:
    async def retrieve(self, request):
        return {
            "results": [],
            "graph": {"nodes": [], "edges": []},
            "evidence": [],
        }


@pytest.mark.asyncio
async def test_reasoning_engine_synthesize_stub_orchestration():
    retriever = _FakeRetriever()
    eng = ReasoningEngine(retriever=retriever)

    req = AnswerRequest(query="Hello", k=2, graph_depth=1)
    resp = await eng.synthesize(req)

    # retriever called exactly once with the same request
    assert retriever.calls == [req]

    # deterministic stub
    assert resp.answer == "(reasoning layer stub)"
    assert resp.confidence == 0.9

    # best-effort ids collected
    assert resp.used_chunks == ["chunk:1", "chunk:2"]
    assert resp.used_nodes == ["node:1", "node:2"]
    assert resp.used_edges == ["edge:1"]

    # provenance validated (malformed skipped)
    assert len(resp.provenance) == 1
    p = resp.provenance[0]
    assert p.type == "chunk"
    assert p.id == "chunk:1"
    assert p.source_refs == ["doc:A#1"]
    assert p.confidence == 0.9

    # context preview packed from provenance source_refs (MVP)
    assert resp.context_preview == "doc:A#1"


@pytest.mark.asyncio
async def test_reasoning_engine_uses_session_memory_when_retrieval_context_empty():
    eng = ReasoningEngine(retriever=_EmptyRetriever())
    req = AnswerRequest(query="follow up", session_memory_last_answer="previous answer from session")

    resp = await eng.synthesize(req)

    assert resp.answer == "(reasoning layer stub)"
    assert resp.context_preview == "previous answer from session"
