from __future__ import annotations

from src.core.config import settings


def test_pro_feature_flags_default_off():
    assert settings.feature_qdrant is False
    assert settings.feature_acl is False
    assert settings.feature_memory is False
    assert settings.feature_graphrag is False
