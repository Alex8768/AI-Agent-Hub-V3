from __future__ import annotations

import pytest

from src.core.config import settings


@pytest.mark.asyncio
async def test_graphrag_pipeline_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    # temp sqlite
    db_path = tmp_path / "test_graphrag.db"
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

    # monkeypatch extractor to avoid real LLM
    from src.layers.pro.graph_rag.contracts.extraction import ExtractionResult, ExtractedEntity, ExtractedRelation, SourceRef

    async def fake_extract(*, workspace_id, document_id, chunk_id, text, **kwargs):
        return ExtractionResult(
            entities=[
                ExtractedEntity(
                    node_type="person",
                    name="Alice",
                    aliases=[],
                    attributes={},
                    confidence=0.9,
                    source_ref=SourceRef(document_id=document_id, chunk_id=chunk_id, snippet="Alice ..."),
                ),
                ExtractedEntity(
                    node_type="person",
                    name="Bob",
                    aliases=[],
                    attributes={},
                    confidence=0.9,
                    source_ref=SourceRef(document_id=document_id, chunk_id=chunk_id, snippet="Bob ..."),
                ),
            ],
            relations=[
                ExtractedRelation(
                    rel_type="mentions",
                    src_name="Alice",
                    src_type="person",
                    dst_name="Bob",
                    dst_type="person",
                    attributes={},
                    confidence=0.8,
                    source_ref=SourceRef(document_id=document_id, chunk_id=chunk_id, snippet="Alice mentions Bob"),
                )
            ],
        )

    import src.layers.pro.graph_rag.extractors.pipeline as pipe
    monkeypatch.setattr(pipe, "extract_from_chunk", fake_extract, raising=True)

    # Run twice
    r1 = await pipe.process_chunk(workspace_id="default", document_id="d1", chunk_id="c1", text="x")
    r2 = await pipe.process_chunk(workspace_id="default", document_id="d1", chunk_id="c1", text="x")
    assert r1["status"] == "ok"
    assert r2["status"] == "ok"
    # Query graph and ensure single edge
    from src.core.providers import get_graph_store
    gs = get_graph_store()

    # Better: search and then neighbors by found node_id
    nodes = await gs.search_nodes(workspace_id="default", text="Alice", limit=10)
    assert nodes
    alice_id = nodes[0]["node_id"]
    sub = await gs.neighbors(workspace_id="default", node_id=alice_id, depth=1, limit=50)
    edge_ids = {e["edge_id"] for e in sub["edges"]}
    assert len(edge_ids) == 1
