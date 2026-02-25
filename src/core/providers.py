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


@dataclass
class NoopMemoryStore:
    """Base-safe memory store: disabled implementation."""
    async def put(self, *, workspace_id: str, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        return None

    async def get(self, *, workspace_id: str, key: str) -> Optional[Any]:
        return None

    async def query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        return []

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
