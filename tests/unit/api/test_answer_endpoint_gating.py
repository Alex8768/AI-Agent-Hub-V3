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

    r_confirm = c.post(
        "/api/v1/answer/confirm",
        json={
            "query": "Q",
            "decision": "cancel",
            "confirmation_token": "confirm:test",
        },
    )
    assert r_confirm.status_code == 404


def test_answer_endpoint_returns_200_when_enabled_unit_stub(monkeypatch):
    # Enable feature gate
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)
    monkeypatch.setattr(s, "feature_assistant_mode", True, raising=False)
    monkeypatch.setattr(s, "feature_assistant_actions", True, raising=False)

    # Avoid heavy RAGEngine init by providing app.state.rag_engine
    app.state.rag_engine = object()

    # Stub HybridRetriever.retrieve to avoid DB/GraphStore access
    import types
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    captured_kwargs: dict = {}

    async def _fake_retrieve(self, **kwargs):
        captured_kwargs.update(kwargs)
        # mimic object with .graph and .evidence attributes used by endpoint adapter
        return types.SimpleNamespace(graph={"nodes": [], "edges": []}, evidence=[])

    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)

    # Endpoint now requires hybrid_retriever to be wired by composition root;
    # for unit-test we stub it in app.state.
    app.state.hybrid_retriever = hr.HybridRetriever()

    c = TestClient(app)
    r = c.post(
        "/api/v1/answer",
        json={
            "query": "Q",
            "evidence_max_total": 17,
            "evidence_max_chunks": 5,
            "evidence_max_memory": 3,
            "evidence_max_edges": 2,
            "evidence_dedupe": False,
            "evidence_rerank": False,
        },
    )
    assert r.status_code == 200

    body = r.json()
    assert body["answer"]  # stub answer
    assert "confidence" in body
    assert "context_preview" in body
    assert captured_kwargs["evidence_max_total"] == 17
    assert captured_kwargs["evidence_max_chunks"] == 5
    assert captured_kwargs["evidence_max_memory"] == 3
    assert captured_kwargs["evidence_max_edges"] == 2
    assert captured_kwargs["evidence_dedupe"] is False
    assert captured_kwargs["evidence_rerank"] is False

    # Best-effort cleanup to reduce state leakage across tests
    try:
        delattr(app.state, "hybrid_retriever")
    except Exception:
        pass


def test_answer_confirm_endpoint_uses_dedicated_contract_surface(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)
    monkeypatch.setattr(s, "feature_assistant_mode", True, raising=False)
    monkeypatch.setattr(s, "feature_assistant_actions", True, raising=False)

    app.state.rag_engine = object()

    import types
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    async def _fake_retrieve(self, **kwargs):
        return types.SimpleNamespace(graph={"nodes": [], "edges": []}, evidence=[], results=[])

    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)
    app.state.hybrid_retriever = hr.HybridRetriever()

    c = TestClient(app)
    prime = c.post("/api/v1/answer", json={"query": "new project planning"})
    assert prime.status_code == 200
    prime_body = prime.json()
    diag = dict(prime_body.get("diagnostics") or {})
    handshake = dict(diag.get("assistant_execution_handshake") or {})
    token = str(handshake.get("confirmation_token", "") or "")
    assert token.startswith("confirm:")

    r = c.post(
        "/api/v1/answer/confirm",
        json={
            "query": "new project planning",
            "decision": "cancel",
            "confirmation_token": token,
            "idempotency_key": "idem-confirm-1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    diag2 = dict(body.get("diagnostics") or {})
    handshake2 = dict(diag2.get("assistant_execution_handshake") or {})
    assert handshake2.get("state") == "cancelled"
    try:
        delattr(app.state, "rag_engine")
    except Exception:
        pass
