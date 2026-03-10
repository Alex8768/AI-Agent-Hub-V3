from __future__ import annotations

from typing import Any

from .contracts import Authorizer, MemoryStore, GraphStoreAPI, NoopAuthorizer, NoopMemoryStore
from .db_wrappers import DBBackedGraphStore, DBBackedMemoryStore


async def get_vector_store():
    """Single entrypoint for vector store selection.

    Base default: calls existing get_vector_store_singleton() (FAISS).
    Pro: routes to Qdrant when settings.feature_qdrant is enabled.
    """
    from src.core.config import settings

    if not getattr(settings, "feature_qdrant", False):
        from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
        return await get_vector_store_singleton()

    from src.layers.pro.rag.vector_stores.factory import get_qdrant_store_singleton
    return await get_qdrant_store_singleton()


def get_authorizer() -> Authorizer:
    from src.core.config import settings
    if getattr(settings, "feature_acl", False):
        from src.security.acl.authorizer import ACLAuthorizer
        return ACLAuthorizer()
    return NoopAuthorizer()


def get_memory_store() -> MemoryStore:
    from src.core.config import settings
    if getattr(settings, "feature_memory", False):
        return DBBackedMemoryStore()
    return NoopMemoryStore()


def get_graph_store() -> GraphStoreAPI | None:
    from src.core.config import settings
    if getattr(settings, "feature_graphrag", False):
        return DBBackedGraphStore()
    return None


def get_reasoning_engine(
    retriever: object | None = None,
    llm: object | None = None,
    llm_timeout_s: float | None = None,
):
    """Return ReasoningEngine instance (Pro), or None when disabled."""
    from src.core.config import get_settings

    s = get_settings()
    if not getattr(s, "feature_reasoning", False):
        return None
    if not getattr(s, "feature_graphrag", False):
        raise RuntimeError("feature_reasoning requires feature_graphrag=True")

    if retriever is None:
        raise RuntimeError("ReasoningEngine requires retriever injection")

    from src.layers.pro.reasoning.kernel import build_reasoning_kernel

    return build_reasoning_kernel(
        retriever=retriever,
        llm=llm,
        llm_timeout_s=llm_timeout_s,
    )
