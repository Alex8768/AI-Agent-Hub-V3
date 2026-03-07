from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings


def test_answer_endpoint_includes_debug_snapshot_when_debug_enabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "debug", True, raising=False)
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
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
    assert diag.get("evidence_contract_version") == "v1"
    assert isinstance(diag.get("evidence_contract_valid_minimal"), bool)
    assert isinstance(diag.get("evidence_contract_missing_minimal_fields"), list)
    assert isinstance(diag.get("evidence_contract_missing_minimal_count"), int)
    assert isinstance(diag.get("evidence_contract_minimal_coverage_score"), float)
    assert isinstance(diag.get("evidence_contract_gate_reason"), str)
    sc = dict(diag.get("self_check") or {})
    assert sc.get("version") == "v1"
    assert sc.get("status") == "pass"
    assert sc.get("reasons") == []
    assert sc.get("policy_mode") == "warning_only"
    sc_inputs = dict(sc.get("inputs") or {})
    assert set(sc_inputs.keys()) == {
        "evidence_contract_valid_minimal",
        "evidence_contract_missing_minimal_count",
        "evidence_contract_minimal_coverage_score",
    }
    assert sc_inputs.get("evidence_contract_valid_minimal") is True
    assert sc_inputs.get("evidence_contract_missing_minimal_count") == 0
    assert sc_inputs.get("evidence_contract_minimal_coverage_score") == 1.0
    sc_thresholds = dict(sc.get("thresholds") or {})
    assert sc_thresholds.get("minimal_coverage_score_min") == 1.0
    assert sc_thresholds.get("missing_minimal_count_max") == 0
    verify = dict(diag.get("verify") or {})
    assert verify.get("version") == "v1"
    assert verify.get("status") == "pass"
    assert verify.get("reasons") == []
    assert verify.get("policy_mode") == "warning_only"
    v_inputs = dict(verify.get("inputs") or {})
    assert v_inputs.get("planner_path_used") is False
    assert v_inputs.get("self_check_status") == "pass"
    assert v_inputs.get("self_check_policy_mode") == "warning_only"
    v_thr = dict(verify.get("thresholds") or {})
    assert v_thr.get("required_self_check_status") == "pass"
    assert v_thr.get("required_self_check_policy_mode") == "warning_only"

    # cleanup
    try:
        delattr(app.state, "hybrid_retriever")
    except Exception:
        pass
    try:
        delattr(app.state, "rag_engine")
    except Exception:
        pass
