from __future__ import annotations

import pytest

from src.services.document.ingest_service import IngestService


class PartialFailVectorStore:
    """Simulates partial vector write then failure."""
    name = "partial-fail-store"

    def __init__(self) -> None:
        self.added_ids: list[str] = []
        self.deleted_ids: list[str] = []

    async def add_documents(self, *, documents, embeddings):
        # add first document id, then fail
        if documents:
            self.added_ids.append(documents[0].id)
        raise RuntimeError("simulated vector store failure")

    async def delete_documents(self, ids):
        self.deleted_ids.extend(list(ids))

    async def get_stats(self):
        return {"ntotal": len(self.added_ids)}

    async def health_check(self):
        return {"status": "healthy"}


@pytest.mark.asyncio
async def test_ingest_rolls_back_partial_vectors_on_failure():
    store = PartialFailVectorStore()
    svc = IngestService(vector_store=store)

    res = await svc.ingest_text(
        "hello world " * 50,
        filename="x.txt",
        metadata={"workspace_id": "default"},
    )
    assert res.success is False

    assert store.added_ids, "expected partial add simulation"
    assert store.deleted_ids == store.added_ids
