from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.services.search.search_service import SearchService


class _FakeEngine:
    async def search(self, **kwargs):
        return []


class _FakeRequest:
    def __init__(self) -> None:
        self.query = "q"
        self.k = 3
        self.filters = None
        self.similarity_threshold = None
        self.include_content = False
        self.include_metadata = False
        self.snippet_len = 120
        self.evidence_max_total = 50
        self.evidence_max_chunks = None
        self.evidence_max_memory = None
        self.evidence_max_edges = None
        self.evidence_dedupe = True
        self.evidence_rerank = True


def _http_stub():
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))


@pytest.mark.asyncio
async def test_search_hybrid_includes_stats_from_object_like_retriever() -> None:
    class _Retriever:
        async def retrieve(self, **kwargs):
            return SimpleNamespace(
                vector_results=[],
                graph={"nodes": [], "edges": []},
                evidence=[],
                stats={"graph_seed_count": 2, "graph_edge_count": 4},
            )

    out = await SearchService().search_hybrid(
        _http_stub(),
        _FakeRequest(),
        workspace_id="default",
        engine=_FakeEngine(),
        retriever=_Retriever(),
    )
    assert out["stats"]["graph_seed_count"] == 2
    assert out["stats"]["graph_edge_count"] == 4


@pytest.mark.asyncio
async def test_search_hybrid_includes_stats_from_dict_like_retriever() -> None:
    class _Retriever:
        async def retrieve(self, **kwargs):
            return {
                "vector_results": [],
                "graph": {"nodes": [], "edges": []},
                "evidence": [],
                "stats": {"graph_enabled": True, "graph_node_count": 3},
            }

    out = await SearchService().search_hybrid(
        _http_stub(),
        _FakeRequest(),
        workspace_id="default",
        engine=_FakeEngine(),
        retriever=_Retriever(),
    )
    assert out["stats"]["graph_enabled"] is True
    assert out["stats"]["graph_node_count"] == 3


@pytest.mark.asyncio
async def test_search_hybrid_forwards_evidence_policy_args() -> None:
    captured: dict = {}

    class _Retriever:
        async def retrieve(self, **kwargs):
            captured.update(kwargs)
            return {"vector_results": [], "graph": {"nodes": [], "edges": []}, "evidence": [], "stats": {}}

    req = _FakeRequest()
    req.evidence_max_total = 17
    req.evidence_max_chunks = 5
    req.evidence_max_memory = 3
    req.evidence_max_edges = 2
    req.evidence_dedupe = False
    req.evidence_rerank = False

    await SearchService().search_hybrid(
        _http_stub(),
        req,
        workspace_id="default",
        engine=_FakeEngine(),
        retriever=_Retriever(),
    )

    assert captured["evidence_max_total"] == 17
    assert captured["evidence_max_chunks"] == 5
    assert captured["evidence_max_memory"] == 3
    assert captured["evidence_max_edges"] == 2
    assert captured["evidence_dedupe"] is False
    assert captured["evidence_rerank"] is False
