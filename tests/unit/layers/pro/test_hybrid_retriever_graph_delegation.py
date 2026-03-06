from __future__ import annotations

import pytest

from src.layers.pro.rag.retrieval.graph_retriever import GraphRetrievalResult
from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever


class _FakeEngine:
    async def search(self, **kwargs):
        return []


class _FakeGraphRetriever:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def retrieve(self, **kwargs):
        self.calls.append(kwargs)
        return GraphRetrievalResult(
            graph={
                "nodes": [{"id": "n1", "name": "Alice"}],
                "edges": [
                    {
                        "id": "e1",
                        "src_id": "n1",
                        "dst_id": "n2",
                        "rel_type": "works_at",
                        "metadata": {"source_refs": ["doc:d1#chunk:c1"], "confidence": 0.8},
                    }
                ],
            },
            evidence=[
                {
                    "type": "edge",
                    "id": "e1",
                    "source_refs": ["doc:d1#chunk:c1"],
                    "confidence": 0.8,
                    "meta": {"rel_type": "works_at", "src_id": "n1", "dst_id": "n2"},
                }
            ],
            seed_ids=["n1"],
            stats={"enabled": True, "seed_count": 1, "node_count": 1, "edge_count": 1},
        )


@pytest.mark.asyncio
async def test_hybrid_retriever_delegates_to_graph_retriever() -> None:
    fake_graph = _FakeGraphRetriever()
    retriever = HybridRetriever(graph_retriever=fake_graph)

    out = await retriever.retrieve(
        engine=_FakeEngine(),
        workspace_id="default",
        query="alice",
        graph_depth=2,
        graph_seed_limit=3,
        graph_limit=10,
    )

    assert len(fake_graph.calls) == 1
    call = fake_graph.calls[0]
    assert call["workspace_id"] == "default"
    assert call["query"] == "alice"
    assert call["graph_depth"] == 2
    assert call["graph_seed_limit"] == 3
    assert call["graph_limit"] == 10

    assert out.graph["nodes"][0]["id"] == "n1"
    assert out.graph["edges"][0]["id"] == "e1"
    edge_evidence = [e for e in out.evidence if e.get("type") == "edge"]
    assert len(edge_evidence) == 1
    assert edge_evidence[0]["id"] == "e1"
    assert edge_evidence[0]["source_refs"] == ["doc:d1#chunk:c1"]
    assert out.stats.get("graph_enabled") is True
    assert out.stats.get("graph_seed_count") == 1
