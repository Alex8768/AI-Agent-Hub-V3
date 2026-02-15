from __future__ import annotations

import asyncio
from typing import Optional

from src.core.config import settings
from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore

_global_vector_store: Optional[FAISSVectorStore] = None
_global_lock: asyncio.Lock = asyncio.Lock()


async def get_vector_store_singleton() -> FAISSVectorStore:
    """
    Global VectorStore singleton.

    Why:
    - Prevent FAISS index reload on every request (IO/CPU storm)
    - Prevent race conditions / index overwrite under concurrency
    - Ensure deterministic, process-wide in-memory state
    """
    global _global_vector_store

    if _global_vector_store is not None:
        return _global_vector_store

    async with _global_lock:
        # Double-check after acquiring the lock
        if _global_vector_store is not None:
            return _global_vector_store

        cfg = settings.get_vector_store_config()
        index_path = getattr(cfg, "path", None) or settings.faiss_index_path
        dimension = getattr(cfg, "dimension", None) or settings.faiss_dimension

        store = FAISSVectorStore(index_path=str(index_path), dimension=int(dimension))
        await store.initialize()
        _global_vector_store = store
        return _global_vector_store
