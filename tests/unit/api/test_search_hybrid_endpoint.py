from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import src.api.main as app_main


def test_search_hybrid_endpoint_returns_404_when_disabled(monkeypatch):
    app = app_main.app
    from src.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "feature_hybrid_search_api", False, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    client = TestClient(app)
    r = client.post("/api/v1/search-hybrid", json={"query": "hello"})
    assert r.status_code == 404


def test_search_hybrid_endpoint_contract(monkeypatch):
    app = app_main.app

    # Enable feature gate for risky Pro endpoint
    from src.core.config import get_settings
    s = get_settings()
    prev_hybrid_api = getattr(s, "feature_hybrid_search_api", False)
    prev_graphrag = getattr(s, "feature_graphrag", False)
    monkeypatch.setattr(s, "feature_hybrid_search_api", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    # Patch get_workspace dependency to avoid auth/workspace complexity
    import src.api.dependencies_impl as deps
    async def _ws(workspace_id=None, user=None):
        return "default"
    monkeypatch.setattr(deps, "get_workspace", _ws, raising=True)

    # Patch HybridRetriever.retrieve to return deterministic payload
    from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetrievalResult

    class DummyDoc:
        def __init__(self):
            self.id = "chunk1"
            self.content = "hello content"
            self.metadata = {"document_id": "doc1", "filename": "a.txt"}

    class DummyResult:
        def __init__(self):
            self.document = DummyDoc()
            self.score = 0.9

    async def _fake_retrieve(self, **kwargs):
        return HybridRetrievalResult(
            vector_results=[DummyResult()],
            graph={"nodes": [{"node_id": "n1"}], "edges": [{"edge_id": "e1", "metadata": {"source_refs": [{"document_id":"doc1","chunk_id":"chunk1","snippet":"x"}]}}]},
            evidence=[{"type": "edge", "edge_id": "e1", "source_refs": [{"document_id":"doc1","chunk_id":"chunk1","snippet":"x"}]}],
            stats={"graph_enabled": True, "graph_seed_count": 1, "graph_edge_count": 1},
        )

    import src.layers.pro.rag.retrieval.hybrid_retriever as hr
    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)

    client = TestClient(app)

    payload = {
        "query": "hello",
        "k": 5,
        "filters": None,
        "similarity_threshold": None,
        "include_content": False,
        "include_metadata": False,
        "snippet_len": 80,
    }

    r = client.post("/api/v1/search-hybrid", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert "results" in data
    assert "graph" in data
    assert "evidence" in data
    assert "stats" in data

    assert isinstance(data["results"], list)
    assert data["graph"]["nodes"]
    assert data["graph"]["edges"]
    assert data["evidence"]
    assert data["stats"]["graph_enabled"] is True
    assert data["stats"]["graph_seed_count"] == 1

    # Restore best-effort
    monkeypatch.setattr(s, "feature_hybrid_search_api", prev_hybrid_api, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", prev_graphrag, raising=False)
