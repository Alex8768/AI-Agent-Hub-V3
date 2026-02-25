from __future__ import annotations

import os
import pytest

from src.core.config import settings


pytestmark = pytest.mark.asyncio


def _env_bool(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).lower() in ("1", "true", "yes", "y", "on")


@pytest.mark.skipif(not _env_bool("RUN_QDRANT_IT", "0"), reason="Qdrant integration tests disabled")
async def test_memory_semantic_put_and_query(tmp_path, monkeypatch):
    # Enable memory + embeddings
    monkeypatch.setattr(settings, "feature_memory", True, raising=False)
    monkeypatch.setattr(settings, "feature_memory_embeddings", True, raising=False)

    # Point DB URL to temp sqlite file
    db_path = tmp_path / "mem_semantic_it.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    import src.infrastructure.database.config as db_config
    monkeypatch.setattr(db_config, "get_database_url", lambda: url, raising=True)

    # Reset engine/sessionmaker
    import src.infrastructure.database.session as db_session
    db_session._engine = None
    db_session._sessionmaker = None

    # IMPORTANT: import model before create_all so it's registered in Base.metadata
    import src.infrastructure.database.models.memory_item  # noqa: F401

    from src.infrastructure.database.base import Base
    from src.infrastructure.database.session import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch embedder to deterministic vectors (avoid heavy model downloads)
    import src.layers.base.rag.embedders.query_embedder as qe

    async def _fake_embed(self, query: str):
        base = 0.2 if ("hello" in query.lower()) else 0.1
        return [base] * 8

    monkeypatch.setattr(qe.QueryEmbedder, "embed_query", _fake_embed, raising=True)

    # Qdrant settings come from CI env
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    monkeypatch.setattr(settings, "qdrant_host", host, raising=False)
    monkeypatch.setattr(settings, "qdrant_port", port, raising=False)

    from src.core.providers import get_memory_store
    mem = get_memory_store()

    await mem.put(workspace_id="default", key="k1", value="hello world", metadata={"tag": "it"})

    hits = await mem.semantic_query(workspace_id="default", text="hello", limit=5)
    assert hits, "expected semantic hits"
    assert hits[0]["key"] == "k1"
