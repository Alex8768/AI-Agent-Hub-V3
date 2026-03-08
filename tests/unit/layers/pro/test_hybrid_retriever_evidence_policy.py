from __future__ import annotations

import pytest

from src.core.config import settings
from src.layers.pro.rag.retrieval.graph_retriever import GraphRetrievalResult
from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever


class _FakeEngine:
    async def search(self, **kwargs):
        return []


class _FakeGraphRetriever:
    async def retrieve(self, **kwargs):
        return GraphRetrievalResult(
            graph={
                "nodes": [{"id": "n1"}],
                "edges": [{"id": "e1", "src_id": "n1", "dst_id": "n2", "rel_type": "related_to"}],
            },
            evidence=[
                {"type": "edge", "id": "e1", "source_refs": ["g1"], "score": 0.9},
                {"type": "edge", "id": "e2", "source_refs": ["g2"], "score": 0.8},
            ],
            seed_ids=["n1"],
            stats={"enabled": True, "seed_count": 1, "node_count": 1, "edge_count": 2},
        )


class _FakeMemoryStore:
    async def semantic_query(self, *, workspace_id: str, text: str, limit: int = 10):
        return [
            {"key": "m1", "score": 0.7, "snippet": "m1"},
            {"key": "m2", "score": 0.6, "snippet": "m2"},
        ]

    async def query(self, *, workspace_id: str, text: str, limit: int = 10):
        return []


@pytest.mark.asyncio
async def test_hybrid_retriever_applies_evidence_budgets(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_memory", True, raising=False)
    monkeypatch.setattr(settings, "feature_memory_embeddings", True, raising=False)
    monkeypatch.setattr(
        "src.layers.pro.rag.retrieval.hybrid_retriever.get_memory_store",
        lambda: _FakeMemoryStore(),
        raising=True,
    )

    retriever = HybridRetriever(graph_retriever=_FakeGraphRetriever())
    out = await retriever.retrieve(
        engine=_FakeEngine(),
        workspace_id="default",
        query="q",
        evidence_max_total=10,
        evidence_max_chunks=0,
        evidence_max_memory=1,
        evidence_max_edges=1,
    )

    types = [x.get("type") for x in out.evidence]
    assert types.count("memory") == 1
    assert types.count("edge") == 1
    assert types.count("chunk") == 0
    assert out.stats.get("evidence_policy_budget_applied") is True
    assert out.stats.get("evidence_policy_budget_memory_used") == 1
    assert out.stats.get("evidence_policy_budget_edges_used") == 1
