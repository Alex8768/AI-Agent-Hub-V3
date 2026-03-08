from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_graph_store_upsert_search_neighbors(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    # Point DB URL to temp sqlite
    db_path = tmp_path / "test_graph.db"
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

    ws = "default"

    await gs.upsert_node(workspace_id=ws, node_id="n1", node_type="entity", name="Alice", metadata={"kind": "person"})
    await gs.upsert_node(workspace_id=ws, node_id="n2", node_type="entity", name="Bob", metadata={"kind": "person"})
    await gs.upsert_edge(workspace_id=ws, edge_id="e1", src_id="n1", dst_id="n2", rel_type="MENTIONS", metadata={"source": "test"})

    # Search should find Alice
    found = await gs.search_nodes(workspace_id=ws, text="Ali", limit=10)
    assert any(n["node_id"] == "n1" for n in found)

    # Neighbors from n1 should include n2 and edge e1
    sub = await gs.neighbors(workspace_id=ws, node_id="n1", depth=1, limit=10)
    node_ids = {n["node_id"] for n in sub["nodes"]}
    edge_ids = {e["edge_id"] for e in sub["edges"]}

    assert "n1" in node_ids
    assert "n2" in node_ids
    assert "e1" in edge_ids

    monkeypatch.setattr(settings, "feature_graphrag", False, raising=False)
