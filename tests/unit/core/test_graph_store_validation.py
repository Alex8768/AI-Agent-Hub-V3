from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_graph_store_rejects_empty_node_id(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    db_path = tmp_path / "test_graph_validation.db"
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

    from src.core.providers import get_graph_store
    gs = get_graph_store()
    assert gs is not None

    with pytest.raises(ValueError):
        await gs.upsert_node(
            workspace_id="default",
            node_id="",
            node_type="entity",
            name="Alice",
            metadata={"kind": "person"},
        )


@pytest.mark.asyncio
async def test_graph_store_rejects_self_loop_edge(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    db_path = tmp_path / "test_graph_validation_2.db"
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

    from src.core.providers import get_graph_store
    gs = get_graph_store()
    assert gs is not None

    with pytest.raises(ValueError):
        await gs.upsert_edge(
            workspace_id="default",
            edge_id="e1",
            src_id="n1",
            dst_id="n1",
            rel_type="MENTIONS",
            metadata={"source": "test"},
        )
