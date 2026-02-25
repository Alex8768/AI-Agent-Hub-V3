from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import src.api.main as app_main


def test_search_hybrid_endpoint_contract(monkeypatch):
    app = app_main.app

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

    assert isinstance(data["results"], list)
    assert data["graph"]["nodes"]
    assert data["graph"]["edges"]
    assert data["evidence"]
