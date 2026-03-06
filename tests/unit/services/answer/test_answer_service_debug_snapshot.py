from __future__ import annotations

import pytest

from src.services.answer.answer_service import AnswerService
from src.layers.pro.reasoning.contracts import AnswerRequest


class _DummyState:
    def __init__(self, request_id: str):
        self.request_id = request_id


class _DummyAppState:
    def __init__(self, rag_engine: object, hybrid_retriever: object):
        self.rag_engine = rag_engine
        self.hybrid_retriever = hybrid_retriever


class _DummyApp:
    def __init__(self, state: _DummyAppState):
        self.state = state


class _DummyHTTP:
    def __init__(self, *, request_id: str, rag_engine: object, hybrid_retriever: object):
        self.state = _DummyState(request_id)
        self.headers = {}
        self.app = _DummyApp(_DummyAppState(rag_engine, hybrid_retriever))


class _FakeHybrid:
    async def retrieve(self, *, engine, workspace_id, query, k, filters, similarity_threshold, graph_depth):
        # minimal evidence with chunk_id so top_evidence becomes chunk:<id>
        return {
            "graph": {"nodes": [], "edges": []},
            "results": [{"id": "r1"}],
            "evidence": [{"chunk_id": "c1", "text": "hello"}],
            "stats": {"vector_candidates_count": 1, "evidence_policy_evidence_after_policy_count": 1},
        }


class _FakeResp:
    def __init__(self):
        self.diagnostics = {}
        self.timings = {}
        self.provenance = []
        self.used_chunks = ['c1']
        self.used_nodes = []
        self.used_edges = []


class _FakeReasoningEngine:
    def __init__(self, retriever):
        self._retriever = retriever

    async def synthesize(self, req):
        # Ensure retriever runs to populate retriever.last_top_evidence
        await self._retriever.retrieve(req)
        return _FakeResp()


@pytest.mark.asyncio
async def test_answer_service_populates_debug_snapshot_fields(monkeypatch):
    # --- settings flags ---
    class _S:
        feature_reasoning = True
        feature_graphrag = True
        feature_reasoning_llm_enabled = False
        llm_provider = "ollama"
        openai_model = ""
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr("src.core.config.get_settings", lambda: _S())

    # --- trace id ---
    monkeypatch.setattr("src.observability.trace.make_trace_id", lambda **kwargs: "trace-123", raising=False)

    # --- providers.get_reasoning_engine should return our fake engine ---
    def _fake_get_reasoning_engine(*, retriever=None, llm=None, llm_timeout_s=None):
        return _FakeReasoningEngine(retriever)

    monkeypatch.setattr("src.core.providers.get_reasoning_engine", _fake_get_reasoning_engine)

    http = _DummyHTTP(request_id="rid-1", rag_engine=object(), hybrid_retriever=_FakeHybrid())
    req = AnswerRequest(query="x", k=8, graph_depth=1, filters={})

    resp = await AnswerService().handle(http, req, workspace_id="default")
    diag = dict(getattr(resp, "diagnostics", {}) or {})

    # Contract keys expected by debug snapshot behavior
    assert "trace_id" in diag
    assert diag["trace_id"] in ("trace-123", "rid-1")

    assert "evidence_type_counts" in diag
    assert isinstance(diag["evidence_type_counts"], dict)

    assert "top_evidence" in diag
    assert isinstance(diag["top_evidence"], list)
    assert any(str(x).startswith("chunk:") for x in diag["top_evidence"])
    rs = (diag.get("retriever_stats") or {})
    assert rs.get("evidence_policy_evidence_after_policy_count") == 1
