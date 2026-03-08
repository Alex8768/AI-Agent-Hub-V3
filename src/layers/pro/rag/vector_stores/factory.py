from __future__ import annotations

import asyncio
from typing import Optional

from src.core.config import settings

_global_qdrant_store = None
_global_lock: asyncio.Lock = asyncio.Lock()


async def get_qdrant_store_singleton():
    """
    Pro Qdrant VectorStore singleton (lazy).

    Note:
    - real adapter is added in PR-2 (this PR)
    - initialization must be idempotent and process-wide
    """
    global _global_qdrant_store

    if _global_qdrant_store is not None:
        return _global_qdrant_store

    async with _global_lock:
        if _global_qdrant_store is not None:
            return _global_qdrant_store

        # Import lazily to keep Base installs clean
        from src.layers.pro.rag.vector_stores.qdrant_store import QdrantVectorStore

        cfg = settings.get_vector_store_config()
        host = getattr(cfg, "host", None) or settings.qdrant_host
        port = getattr(cfg, "port", None) or settings.qdrant_port
        collection = getattr(cfg, "collection", None) or settings.qdrant_collection
        timeout = getattr(cfg, "timeout", None) or settings.qdrant_timeout

        store = QdrantVectorStore(host=str(host), port=int(port), collection=str(collection), timeout=int(timeout))
        await store.initialize()
        _global_qdrant_store = store
        return _global_qdrant_store
