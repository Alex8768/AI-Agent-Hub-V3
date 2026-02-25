from __future__ import annotations

from src.core.config import settings


def test_feature_memory_embeddings_default_off():
    assert settings.feature_memory_embeddings is False
