from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_feature_qdrant_routes_to_qdrant_store(monkeypatch):
    # Enable flag
    monkeypatch.setattr(settings, "feature_qdrant", True, raising=False)

    # Patch QdrantVectorStore.initialize to avoid network/server dependency
    from src.layers.pro.rag.vector_stores import qdrant_store as qs

    async def _noop_init(self):
        self._initialized = True
        self._client = object()
        self._dim = None

    monkeypatch.setattr(qs.QdrantVectorStore, "initialize", _noop_init, raising=True)

    from src.core.providers import get_vector_store

    store = await get_vector_store()
    assert getattr(store, "name", "") == "qdrant"

    # Restore (defensive)
    monkeypatch.setattr(settings, "feature_qdrant", False, raising=False)
