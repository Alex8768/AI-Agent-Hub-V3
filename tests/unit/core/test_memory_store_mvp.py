from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_memory_store_put_get_query(tmp_path, monkeypatch):
    # Enable memory feature
    monkeypatch.setattr(settings, "feature_memory", True, raising=False)

    # Point DB URL to a temp sqlite file
    db_path = tmp_path / "test_memory.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    # Patch get_database_url()
    import src.infrastructure.database.config as db_config
    monkeypatch.setattr(db_config, "get_database_url", lambda: url, raising=True)

    # Reset engine/sessionmaker singletons
    import src.infrastructure.database.session as db_session
    db_session._engine = None
    db_session._sessionmaker = None

    # Create tables
    from src.infrastructure.database.base import Base
    from src.infrastructure.database.session import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Use providers facade
    from src.core.providers import get_memory_store
    mem = get_memory_store()

    ws = "default"

    await mem.put(workspace_id=ws, key="k1", value="hello world", metadata={"tag": "x"})
    v = await mem.get(workspace_id=ws, key="k1")
    assert v == "hello world"

    res = await mem.query(workspace_id=ws, text="hello", limit=10)
    assert any(r["key"] == "k1" for r in res)

    # cleanup
    monkeypatch.setattr(settings, "feature_memory", False, raising=False)
