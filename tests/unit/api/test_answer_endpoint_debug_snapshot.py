from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings


def test_answer_endpoint_includes_debug_snapshot_when_debug_enabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "debug", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    # Provide required state deps
    app.state.rag_engine = object()

    import types
    import src.layers.pro.rag.retrieval.hybrid_retriever as hr

    async def _fake_retrieve(self, **kwargs):
        # Provide some evidence that becomes provenance
        return types.SimpleNamespace(
            graph={"nodes": [{"id": "n1"}], "edges": [{"id": "e1"}]},
            evidence=[
                {"type": "chunk", "id": "c1", "source_refs": ["doc1"], "score": 1.0},
                {"type": "memory", "id": "m1", "source_refs": ["mem"], "score": 0.9},
                {"type": "edge", "id": "e1", "source_refs": ["g"], "confidence": 0.5},
            ],
            results=[{"chunk_id": "c1"}],
            stats={"memory_mode": "semantic", "memory_candidates_count": 1, "memory_added_evidence_count": 1},
        )

    monkeypatch.setattr(hr.HybridRetriever, "retrieve", _fake_retrieve, raising=True)
    app.state.hybrid_retriever = hr.HybridRetriever()

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 200
    body = r.json()

    diag = body.get("diagnostics") or {}
    assert "trace_id" in diag
    assert "evidence_type_counts" in diag
    assert "top_evidence" in diag
    assert isinstance(diag["top_evidence"], list)
    assert any(x.startswith("chunk:") for x in diag["top_evidence"])

    # cleanup
    try:
        delattr(app.state, "hybrid_retriever")
    except Exception:
        pass
    try:
        delattr(app.state, "rag_engine")
    except Exception:
        pass
