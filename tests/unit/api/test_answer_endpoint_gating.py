from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings


def test_answer_endpoint_returns_404_when_disabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning", False, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 404


def test_answer_endpoint_returns_501_when_enabled_but_not_wired(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning", True, raising=False)
    monkeypatch.setattr(s, "feature_graphrag", True, raising=False)

    c = TestClient(app)
    r = c.post("/api/v1/answer", json={"query": "Q"})
    assert r.status_code == 501
