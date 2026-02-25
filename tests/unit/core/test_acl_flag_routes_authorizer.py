from __future__ import annotations

from src.core.config import settings


def test_feature_acl_routes_to_acl_authorizer(monkeypatch):
    monkeypatch.setattr(settings, "feature_acl", True, raising=False)

    from src.core.providers import get_authorizer
    auth = get_authorizer()

    assert auth.__class__.__name__ == "ACLAuthorizer"

    monkeypatch.setattr(settings, "feature_acl", False, raising=False)
