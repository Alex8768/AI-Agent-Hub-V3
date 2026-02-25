from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


# -------------------------
# Pro-side minimal contracts (Base-safe defaults)
# -------------------------

class Authorizer(Protocol):
    def can_read(self, *, workspace_id: str, user: dict[str, Any], resource: str, resource_id: Optional[str] = None) -> bool: ...
    def can_write(self, *, workspace_id: str, user: dict[str, Any], resource: str, resource_id: Optional[str] = None) -> bool: ...


@dataclass(frozen=True)
class NoopAuthorizer:
    """Base-safe authorizer: allow everything within already-validated workspace boundary."""
    def can_read(self, *, workspace_id: str, user: dict[str, Any], resource: str, resource_id: Optional[str] = None) -> bool:
        return True

    def can_write(self, *, workspace_id: str, user: dict[str, Any], resource: str, resource_id: Optional[str] = None) -> bool:
        return True


class MemoryStore(Protocol):
    async def put(self, *, workspace_id: str, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None: ...
    async def get(self, *, workspace_id: str, key: str) -> Optional[Any]: ...
    async def query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]: ...
    async def semantic_query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]: ...


class GraphStoreAPI(Protocol):
    async def upsert_node(self, *, workspace_id: str, node_id: str, node_type: str, name: str, metadata: Optional[dict[str, Any]] = None) -> None: ...
    async def upsert_edge(self, *, workspace_id: str, edge_id: str, src_id: str, dst_id: str, rel_type: str, metadata: Optional[dict[str, Any]] = None) -> None: ...
    async def search_nodes(self, *, workspace_id: str, text: str, limit: int = 20) -> list[dict[str, Any]]: ...
    async def neighbors(self, *, workspace_id: str, node_id: str, depth: int = 1, limit: int = 50) -> dict[str, Any]: ...


@dataclass
class DBBackedGraphStore:
    """DB-backed GraphStore wrapper (no DI required)."""

    async def upsert_node(self, *, workspace_id: str, node_id: str, node_type: str, name: str, metadata: Optional[dict[str, Any]] = None) -> None:
        from src.infrastructure.database import get_db
        from src.layers.pro.graph_rag.graph.store import GraphStore

        async with get_db() as db:
            store = GraphStore(db)
            await store.upsert_node(workspace_id=workspace_id, node_id=node_id, node_type=node_type, name=name, metadata=metadata)

    async def upsert_edge(self, *, workspace_id: str, edge_id: str, src_id: str, dst_id: str, rel_type: str, metadata: Optional[dict[str, Any]] = None) -> None:
        from src.infrastructure.database import get_db
        from src.layers.pro.graph_rag.graph.store import GraphStore

        async with get_db() as db:
            store = GraphStore(db)
            await store.upsert_edge(workspace_id=workspace_id, edge_id=edge_id, src_id=src_id, dst_id=dst_id, rel_type=rel_type, metadata=metadata)

    async def search_nodes(self, *, workspace_id: str, text: str, limit: int = 20) -> list[dict[str, Any]]:
        from src.infrastructure.database import get_db
        from src.layers.pro.graph_rag.graph.store import GraphStore

        async with get_db() as db:
            store = GraphStore(db)
            return await store.search_nodes(workspace_id=workspace_id, text=text, limit=limit)

    async def neighbors(self, *, workspace_id: str, node_id: str, depth: int = 1, limit: int = 50) -> dict[str, Any]:
        from src.infrastructure.database import get_db
        from src.layers.pro.graph_rag.graph.store import GraphStore

        async with get_db() as db:
            store = GraphStore(db)
            return await store.neighbors(workspace_id=workspace_id, node_id=node_id, depth=depth, limit=limit)




@dataclass
class NoopMemoryStore:
    """Base-safe memory store: disabled implementation."""
    async def put(self, *, workspace_id: str, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        return None

    async def get(self, *, workspace_id: str, key: str) -> Optional[Any]:
        return None

    async def query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        return []

    async def semantic_query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        raise RuntimeError("Semantic memory embeddings are disabled")

@dataclass
class DBBackedMemoryStore:
    """DB-backed MemoryStore wrapper (no DI required).

    Opens DB session per call using src.infrastructure.database.get_db().
    Internally delegates to SQLiteMemoryStore.
    """

    async def put(self, *, workspace_id: str, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        from src.infrastructure.database import get_db
        from src.layers.pro.memory.stores.sqlite_memory_store import SQLiteMemoryStore

        async with get_db() as db:
            store = SQLiteMemoryStore(db)
            await store.put(workspace_id=workspace_id, key=key, value=value, metadata=metadata)

        # Semantic memory embeddings index (Pro, optional)
        from src.core.config import settings
        if getattr(settings, "feature_memory_embeddings", False):
            from src.layers.base.rag.embedders.query_embedder import QueryEmbedder
            from src.layers.pro.memory.indexing.qdrant_memory_index import QdrantMemoryIndex

            embedder = QueryEmbedder()
            vec = await embedder.embed_query(str(value))

            index = QdrantMemoryIndex(
                host=str(getattr(settings, "qdrant_host", "localhost")),
                port=int(getattr(settings, "qdrant_port", 6333)),
                timeout=int(getattr(settings, "qdrant_timeout", 10)),
            )
            await index.upsert(
                workspace_id=workspace_id,
                key=key,
                text=str(value),
                embedding=vec,
                metadata=metadata,
            )

    async def get(self, *, workspace_id: str, key: str) -> Optional[Any]:
        from src.infrastructure.database import get_db
        from src.layers.pro.memory.stores.sqlite_memory_store import SQLiteMemoryStore

        async with get_db() as db:
            store = SQLiteMemoryStore(db)
            return await store.get(workspace_id=workspace_id, key=key)

    async def query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        from src.infrastructure.database import get_db
        from src.layers.pro.memory.stores.sqlite_memory_store import SQLiteMemoryStore

        async with get_db() as db:
            store = SQLiteMemoryStore(db)
            return await store.query(workspace_id=workspace_id, text=text, limit=limit)

    async def semantic_query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        """Semantic memory search via Qdrant index (requires feature_memory_embeddings)."""
        from src.core.config import settings
        if not getattr(settings, "feature_memory_embeddings", False):
            raise RuntimeError("Semantic memory embeddings are disabled")

        from src.layers.base.rag.embedders.query_embedder import QueryEmbedder
        from src.layers.pro.memory.indexing.qdrant_memory_index import QdrantMemoryIndex

        embedder = QueryEmbedder()
        qvec = await embedder.embed_query(text)

        index = QdrantMemoryIndex(
            host=str(getattr(settings, "qdrant_host", "localhost")),
            port=int(getattr(settings, "qdrant_port", 6333)),
            timeout=int(getattr(settings, "qdrant_timeout", 10)),
        )
        return await index.search(workspace_id=workspace_id, query_embedding=qvec, limit=int(limit))




# -------------------------
# Facade providers (single entry for feature flags)
# -------------------------

async def get_vector_store():
    """
    Single entrypoint for vector store selection.
    Base default: calls existing get_vector_store_singleton() (FAISS).
    Pro: will route to Qdrant when settings.feature_qdrant is enabled.
    """
    from src.core.config import settings

    # Base route
    if not getattr(settings, "feature_qdrant", False):
        from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
        return await get_vector_store_singleton()

    # Pro route
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
    """Return ReasoningEngine instance (Pro), or None when disabled.

    Strict rules:
      - feature_reasoning must be enabled
      - feature_graphrag must be enabled (reasoning is graph-aware)
      - Reasoning lives in Pro layer; Base must remain untouched

    DI rule:
      - retriever must be injected by the composition root (API/service layer)
      - llm may be injected (optional; when absent engine returns stub)
      - llm_timeout_s may be injected (optional override)
    """
    from src.core.config import get_settings

    s = get_settings()
    if not getattr(s, "feature_reasoning", False):
        return None
    if not getattr(s, "feature_graphrag", False):
        raise RuntimeError("feature_reasoning requires feature_graphrag=True")

    if retriever is None:
        raise RuntimeError("ReasoningEngine requires retriever injection")

    # Import lazily to keep Base import graph clean.
    from src.layers.pro.reasoning.engine import ReasoningEngine

    if llm_timeout_s is None:
        return ReasoningEngine(retriever=retriever, llm=llm)
    return ReasoningEngine(retriever=retriever, llm=llm, llm_timeout_s=float(llm_timeout_s))
