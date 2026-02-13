import pytest

from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore


@pytest.mark.asyncio
async def test_faiss_initialize_is_idempotent(monkeypatch, tmp_path):
    store = FAISSVectorStore(index_path=str(tmp_path / "faiss_index"), dimension=384)

    calls = {"n": 0}
    original = store._initialize_faiss

    async def wrapped():
        calls["n"] += 1
        return await original()

    monkeypatch.setattr(store, "_initialize_faiss", wrapped)

    await store.initialize()
    await store.initialize()

    assert calls["n"] == 1
