from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings


def test_answer_endpoint_returns_404_when_disabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", False, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", False, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 404


def test_answer_endpoint_returns_404_when_reasoning_api_flag_off(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", False, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 404


def test_answer_endpoint_returns_200_when_enabled_unit_stub(monkeypatch):
    # Enable feature gate
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    # Avoid heavy RAGEngine init by providing app.state.rag_engine
    app.state.rag_engine = object()

    # Stub HybridRetriever.retrieve to avoid DB/GraphStore access
    import types
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    async def _fake_retrieve(self, **kwargs):
        # mimic object with .graph and .evidence attributes used by endpoint adapter
        return types.SimpleNamespace(graph={"nodes": [], "edges": []}, evidence=[])

    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)

    # Endpoint now requires hybrid_retriever to be wired by composition root;
    # for unit-test we stub it in app.state.
    app.state.hybrid_retriever = hr.HybridRetriever()

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 200

    body = r.json()
    assert body["answer"]  # stub answer
    assert "confidence" in body
    assert "context_preview" in body

    # Best-effort cleanup to reduce state leakage across tests
    try:
        delattr(app.state, "hybrid_retriever")
    except Exception:
        pass
    try:
        delattr(app.state, "rag_engine")
    except Exception:
        pass
