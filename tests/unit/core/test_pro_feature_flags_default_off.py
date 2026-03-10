from __future__ import annotations

from src.core.config import Settings


def test_pro_feature_flags_default_off():
    settings = Settings(_env_file=None)
    assert settings.feature_qdrant is False
    assert settings.feature_acl is False
    assert settings.feature_memory is False
    assert settings.feature_graphrag is False
    assert settings.feature_assistant_mode is False
    assert settings.feature_assistant_proactive is False
    assert settings.feature_assistant_actions is False
