from __future__ import annotations

import os
import uuid

import pytest

from src.core.contracts import VectorDocument


pytestmark = pytest.mark.asyncio


def _env_bool(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).lower() in ("1", "true", "yes", "y", "on")


@pytest.mark.skipif(not _env_bool("RUN_QDRANT_IT", "0"), reason="Qdrant integration tests disabled")
async def test_qdrant_add_search_delete_roundtrip(monkeypatch):
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))

    # Use unique collection per run to avoid collisions
    collection = f"ai_agent_hub_it_{uuid.uuid4().hex[:10]}"

    # Patch settings for this test run
    from src.core.config import settings
    monkeypatch.setattr(settings, "feature_qdrant", True, raising=False)
    monkeypatch.setattr(settings, "qdrant_host", host, raising=False)
    monkeypatch.setattr(settings, "qdrant_port", port, raising=False)
    monkeypatch.setattr(settings, "qdrant_collection", collection, raising=False)

    # Import after settings patch
    from src.core.providers import get_vector_store
    store = await get_vector_store()

    # Prepare one document with a simple embedding
    emb_dim = 8
    doc_id = str(uuid.uuid4())
    doc = VectorDocument(
        id=doc_id,
        content="hello qdrant",
        metadata={"workspace_id": "default", "tag": "it"},
        embedding=None,
    )
    embedding = [0.1] * emb_dim

    # Add
    ids = await store.add_documents([doc], embeddings=[embedding])
    assert ids == [doc_id]

    # Search (same embedding)
    results = await store.search("hello", query_embedding=embedding, k=5, filter={"tag": "it"})
    assert any(r.document.id == doc_id for r in results)

    # Delete
    deleted = await store.delete([doc_id])
    assert deleted >= 1

    # Search again -> should be empty
    results2 = await store.search("hello", query_embedding=embedding, k=5, filter={"tag": "it"})
    assert all(r.document.id != doc_id for r in results2)
