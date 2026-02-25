from __future__ import annotations

import importlib
import pytest


def test_get_reasoning_engine_returns_none_when_disabled(monkeypatch):
    cfg = importlib.import_module("src.core.config")
    providers = importlib.import_module("src.core.providers")

    settings = cfg.get_settings()

    # Force flags OFF
    monkeypatch.setattr(settings, "feature_reasoning", False, raising=False)
    monkeypatch.setattr(settings, "feature_graphrag", False, raising=False)

    assert providers.get_reasoning_engine() is None


def test_get_reasoning_engine_requires_graphrag(monkeypatch):
    cfg = importlib.import_module("src.core.config")
    providers = importlib.import_module("src.core.providers")

    settings = cfg.get_settings()

    # Reasoning ON, GraphRAG OFF => fail-fast
    monkeypatch.setattr(settings, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(settings, "feature_graphrag", False, raising=False)

    with pytest.raises(RuntimeError):
        providers.get_reasoning_engine()
