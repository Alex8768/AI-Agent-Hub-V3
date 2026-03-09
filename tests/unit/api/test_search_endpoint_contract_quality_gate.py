from __future__ import annotations

from fastapi.testclient import TestClient

import src.api.main as app_main
from src.services.search.contracts import SearchServiceResult
from src.services.search.search_service import SearchService


def test_search_endpoint_quality_gate_deterministic_contract(monkeypatch):
    app = app_main.app

    import src.api.dependencies_impl as deps

    async def _ws(workspace_id=None, user=None):
        return "default"

    monkeypatch.setattr(deps, "get_workspace", _ws, raising=True)

    async def _fake_search(self, http, request, *, workspace_id, engine=None):
        return [
            SearchServiceResult(
                chunk_id="chunk-1",
                document_id="doc-1",
                score=0.91,
                snippet="hello",
                content=None,
                source_document="a.txt",
                metadata={},
            )
        ]

    monkeypatch.setattr(SearchService, "search", _fake_search, raising=True)

    client = TestClient(app)
    payload = {"query": "hello", "k": 5, "include_content": False, "include_metadata": True}

    r1 = client.post("/api/v1/search", json=payload)
    r2 = client.post("/api/v1/search", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert r1.json() == [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "score": 0.91,
            "snippet": "hello",
            "content": None,
            "source_document": "a.txt",
            "metadata": {},
        }
    ]


def test_search_hybrid_endpoint_quality_gate_contract_parity(monkeypatch):
    app = app_main.app

    from src.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "feature_hybrid_search_api", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    import src.api.dependencies_impl as deps

    async def _ws(workspace_id=None, user=None):
        return "default"

    monkeypatch.setattr(deps, "get_workspace", _ws, raising=True)

    async def _fake_search_hybrid(self, http, request, *, workspace_id, graph_depth=1, engine=None, retriever=None):
        return {
            "results": [
                SearchServiceResult(
                    chunk_id="chunk-2",
                    document_id="doc-2",
                    score=0.77,
                    snippet="world",
                    content=None,
                    source_document="b.txt",
                    metadata={"tag": "x"},
                ),
                {
                    "chunk_id": "chunk-3",
                    "document_id": "doc-3",
                    "score": 0.66,
                    "snippet": "third",
                    "content": None,
                    "source_document": "c.txt",
                    "metadata": {},
                },
            ],
            "graph": {"nodes": [{"id": "n1"}], "edges": []},
            "evidence": [{"type": "chunk", "id": "chunk-2"}],
            "stats": {"graph_enabled": True},
        }

    monkeypatch.setattr(SearchService, "search_hybrid", _fake_search_hybrid, raising=True)

    client = TestClient(app)
    payload = {"query": "hello", "k": 5}
    r = client.post("/api/v1/search-hybrid", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"results", "graph", "evidence", "stats"}
    assert len(data["results"]) == 2
    assert data["results"][0]["chunk_id"] == "chunk-2"
    assert data["results"][1]["chunk_id"] == "chunk-3"
    assert data["graph"]["nodes"][0]["id"] == "n1"
    assert data["stats"]["graph_enabled"] is True
