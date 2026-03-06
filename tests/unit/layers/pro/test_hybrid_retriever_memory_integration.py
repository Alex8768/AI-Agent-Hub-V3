from __future__ import annotations

import pytest

from src.core.config import get_settings
from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever


@pytest.mark.asyncio
async def test_hybrid_retriever_includes_memory_evidence_when_enabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_memory", True, raising=False)
    monkeypatch.setattr(s, "feature_memory_embeddings", True, raising=False)

    class FakeEngine:
        async def search(self, **kwargs):
            return []  # no vector hits

    class FakeMemoryStore:
        async def semantic_query(self, *, workspace_id: str, text: str, limit: int = 10):
            return [
                {"key": "k1", "score": 0.9, "snippet": "hello", "payload": {"workspace_id": workspace_id}},
                {"key": "k2", "score": 0.8, "snippet": "world", "payload": {"workspace_id": workspace_id}},
            ]

        async def query(self, *, workspace_id: str, text: str, limit: int = 10):
            return []

    # Monkeypatch provider accessor used in hybrid_retriever module
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    monkeypatch.setattr(hr, "get_memory_store", lambda: FakeMemoryStore(), raising=True)

    out = await HybridRetriever().retrieve(engine=FakeEngine(), workspace_id="default", query="Q", k=5)

    mem = [e for e in out.evidence if e.get("type") == "memory"]
    assert len(mem) == 2
    assert {m.get("id") for m in mem} == {"k1", "k2"}
