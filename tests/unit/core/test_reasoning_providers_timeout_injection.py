from __future__ import annotations

import importlib


class _FakeRetriever:
    async def retrieve(self, request):
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


def test_get_reasoning_engine_injects_timeout(monkeypatch):
    cfg = importlib.import_module("src.core.config")
    providers = importlib.import_module("src.core.providers")

    settings = cfg.get_settings()
    monkeypatch.setattr(settings, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    eng = providers.get_reasoning_engine(retriever=_FakeRetriever(), llm=None, llm_timeout_s=3.5)
    assert eng is not None
    assert getattr(eng, "llm_timeout_s") == 3.5
