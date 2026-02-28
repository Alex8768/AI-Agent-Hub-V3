from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


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
