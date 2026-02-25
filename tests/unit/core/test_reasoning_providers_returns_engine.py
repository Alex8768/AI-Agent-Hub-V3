from __future__ import annotations

import importlib


class _FakeRetriever:
    async def retrieve(self, request):
        return {"results": [], "graph": {"nodes": [], "edges": []}, "evidence": []}


def test_get_reasoning_engine_returns_instance_when_enabled(monkeypatch):
    cfg = importlib.import_module("src.core.config")
    providers = importlib.import_module("src.core.providers")

    settings = cfg.get_settings()
    monkeypatch.setattr(settings, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    eng = providers.get_reasoning_engine(retriever=_FakeRetriever())
    assert eng is not None
    assert eng.__class__.__name__ == "ReasoningEngine"
    assert eng.__class__.__module__ == "src.layers.pro.reasoning.engine"
