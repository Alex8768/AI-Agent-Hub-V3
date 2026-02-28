from __future__ import annotations

import importlib
import sys


def test_nodes_import_without_opentelemetry(monkeypatch):
    # Simulate missing opentelemetry even if installed locally
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    sys.modules.pop("src.layers.pro.reasoning.graph.nodes", None)

    m = importlib.import_module("src.layers.pro.reasoning.graph.nodes")
    assert hasattr(m, "trace")
    assert hasattr(m.trace, "get_tracer")
