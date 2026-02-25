from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_memory_put_calls_qdrant_indexer_when_enabled(tmp_path, monkeypatch):
    # Enable memory + embeddings feature
    monkeypatch.setattr(settings, "feature_memory", True, raising=False)
    monkeypatch.setattr(settings, "feature_memory_embeddings", True, raising=False)

    # Patch DB url to temp sqlite
    db_path = tmp_path / "test_mem_semantic.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    import src.infrastructure.database.config as db_config
    monkeypatch.setattr(db_config, "get_database_url", lambda: url, raising=True)

    import src.infrastructure.database.session as db_session
    db_session._engine = None
    db_session._sessionmaker = None

    from src.infrastructure.database.base import Base
    from src.infrastructure.database.session import get_engine
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch embedder
    import src.layers.base.rag.embedders.query_embedder as qe

    async def _fake_embed(self, query: str):
        return [0.1] * 8

    monkeypatch.setattr(qe.QueryEmbedder, "embed_query", _fake_embed, raising=True)

    # Patch QdrantMemoryIndex methods to avoid network
    import src.layers.pro.memory.indexing.qdrant_memory_index as mi

    calls = {"upsert": 0, "search": 0}

    async def _fake_upsert(self, **kwargs):
        calls["upsert"] += 1
        return None

    async def _fake_search(self, **kwargs):
        calls["search"] += 1
        return [{"key": "k1", "score": 0.9, "snippet": "hello", "payload": {"key": "k1"}}]

    monkeypatch.setattr(mi.QdrantMemoryIndex, "upsert", _fake_upsert, raising=True)
    monkeypatch.setattr(mi.QdrantMemoryIndex, "search", _fake_search, raising=True)

    from src.core.providers import get_memory_store
    mem = get_memory_store()

    await mem.put(workspace_id="default", key="k1", value="hello world", metadata={"tag": "x"})
    assert calls["upsert"] == 1

    hits = await mem.semantic_query(workspace_id="default", text="hello", limit=5)
    assert calls["search"] == 1
    assert hits and hits[0]["key"] == "k1"

    # Restore flags
    monkeypatch.setattr(settings, "feature_memory_embeddings", False, raising=False)
    monkeypatch.setattr(settings, "feature_memory", False, raising=False)


@pytest.mark.asyncio
async def test_semantic_query_raises_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "feature_memory_embeddings", False, raising=False)

    from src.core.providers import get_memory_store
    mem = get_memory_store()

    with pytest.raises(RuntimeError):
        await mem.semantic_query(workspace_id="default", text="x", limit=3)
