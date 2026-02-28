from __future__ import annotations

import importlib
import sys


def test_tracing_setup_import_without_opentelemetry(monkeypatch):
    # Simulate missing opentelemetry even if installed locally
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    sys.modules.pop("src.observability.tracing.setup", None)

    m = importlib.import_module("src.observability.tracing.setup")
    assert hasattr(m, "setup_tracing")
    assert hasattr(m, "trace")
