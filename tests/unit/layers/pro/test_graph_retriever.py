from __future__ import annotations

import pytest

from src.core.config import settings
from src.layers.pro.rag.retrieval.graph_retriever import GraphRetriever


class _FakeGraphStore:
    async def search_nodes(self, *, workspace_id: str, text: str, limit: int = 20):
        return [{"node_id": "n1"}, {"node_id": "n2"}]

    async def neighbors(self, *, workspace_id: str, node_id: str, depth: int = 1, limit: int = 50):
        if node_id == "n1":
            return {
                "nodes": [
                    {"node_id": "n1", "name": "Alice"},
                    {"node_id": "n2", "name": "ACME"},
                ],
                "edges": [
                    {"edge_id": "e1", "src_id": "n1", "dst_id": "n2", "rel_type": "works_at"},
                ],
            }
        return {
            "nodes": [
                {"node_id": "n2", "name": "ACME"},
                {"node_id": "n3", "name": "London"},
            ],
            "edges": [
                {"edge_id": "e1", "src_id": "n1", "dst_id": "n2", "rel_type": "works_at"},
                {"edge_id": "e2", "src_id": "n2", "dst_id": "n3", "rel_type": "located_in"},
            ],
        }


@pytest.mark.asyncio
async def test_graph_retriever_returns_empty_when_feature_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", False, raising=False)
    retriever = GraphRetriever()

    res = await retriever.retrieve(workspace_id="w1", query="alice")
    assert res.graph == {"nodes": [], "edges": []}
    assert res.seed_ids == []
    assert res.stats.get("enabled") is False
    assert res.stats.get("reason") == "feature_graphrag_off"


@pytest.mark.asyncio
async def test_graph_retriever_returns_empty_when_store_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)
    monkeypatch.setattr(
        "src.layers.pro.rag.retrieval.graph_retriever.get_graph_store",
        lambda: None,
        raising=True,
    )
    retriever = GraphRetriever()

    res = await retriever.retrieve(workspace_id="w1", query="alice")
    assert res.graph == {"nodes": [], "edges": []}
    assert res.seed_ids == []
    assert res.stats.get("enabled") is False
    assert res.stats.get("reason") == "graph_store_unavailable"


@pytest.mark.asyncio
async def test_graph_retriever_collects_and_deduplicates_graph(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)
    monkeypatch.setattr(
        "src.layers.pro.rag.retrieval.graph_retriever.get_graph_store",
        lambda: _FakeGraphStore(),
        raising=True,
    )
    retriever = GraphRetriever()

    res = await retriever.retrieve(
        workspace_id="w1",
        query="alice",
        graph_depth=2,
        graph_seed_limit=5,
        graph_limit=50,
    )
    assert res.seed_ids == ["n1", "n2"]
    node_ids = {n["id"] for n in res.graph["nodes"]}
    edge_ids = {e["id"] for e in res.graph["edges"]}
    assert node_ids == {"n1", "n2", "n3"}
    assert edge_ids == {"e1", "e2"}
    assert res.stats.get("enabled") is True
    assert res.stats.get("seed_count") == 2
    assert res.stats.get("node_count") == 3
    assert res.stats.get("edge_count") == 2
