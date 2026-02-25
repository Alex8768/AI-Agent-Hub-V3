from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.core.exceptions import VectorStoreError


def _require_qdrant_client() -> Dict[str, Any]:
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue  # type: ignore
        return {
            "QdrantClient": QdrantClient,
            "Distance": Distance,
            "VectorParams": VectorParams,
            "PointStruct": PointStruct,
            "Filter": Filter,
            "FieldCondition": FieldCondition,
            "MatchValue": MatchValue,
        }
    except Exception as e:
        raise VectorStoreError(
            message="Qdrant client is not installed. Install Pro extras to enable memory embeddings.",
            operation="initialize",
            details={"error": str(e)},
        ) from e


@dataclass
class QdrantMemoryIndex:
    host: str
    port: int
    collection: str = "memory_items"
    timeout: int = 10

    _client: Any = None
    _initialized: bool = False
    _dim: Optional[int] = None

    async def initialize(self) -> None:
        if self._initialized:
            return

        mods = _require_qdrant_client()
        QdrantClient = mods["QdrantClient"]
        try:
            self._client = QdrantClient(host=self.host, port=self.port, timeout=self.timeout, check_compatibility=False)
        except TypeError:
            self._client = QdrantClient(host=self.host, port=self.port, timeout=self.timeout)

        self._initialized = True

    async def _ensure_collection(self, dim: int) -> None:
        mods = _require_qdrant_client()
        Distance = mods["Distance"]
        VectorParams = mods["VectorParams"]

        try:
            info = self._client.get_collection(self.collection)
            try:
                existing_dim = int(info.config.params.vectors.size)  # type: ignore[attr-defined]
                if existing_dim != dim:
                    raise VectorStoreError(
                        message=f"Memory Qdrant dimension mismatch: collection={existing_dim} embedder={dim}",
                        operation="initialize",
                        details={"collection": self.collection, "collection_dim": existing_dim, "embedder_dim": dim},
                    )
            except Exception:
                pass
        except Exception:
            self._client.recreate_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=int(dim), distance=Distance.COSINE),
            )

        self._dim = dim

    def _point_id(self, workspace_id: str, key: str) -> str:
        return f"memory:{workspace_id}:{key}"

    async def upsert(
        self,
        *,
        workspace_id: str,
        key: str,
        text: str,
        embedding: List[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        if not self._initialized:
            await self.initialize()

        dim = len(embedding)
        if dim <= 0:
            raise VectorStoreError("Invalid embedding dimension", operation="memory_upsert", details={"dimension": dim})

        await self._ensure_collection(dim)

        mods = _require_qdrant_client()
        PointStruct = mods["PointStruct"]

        payload = dict(metadata or {})
        payload["workspace_id"] = workspace_id
        payload["key"] = key
        payload["snippet"] = text[:240]

        pid = self._point_id(workspace_id, key)
        point = PointStruct(id=pid, vector=embedding, payload=payload)

        try:
            self._client.upsert(collection_name=self.collection, points=[point])
        except Exception as e:
            raise VectorStoreError(
                message=f"Memory upsert failed: {e}",
                operation="memory_upsert",
                details={"collection": self.collection, "workspace_id": workspace_id, "key": key},
            ) from e

    async def search(
        self,
        *,
        workspace_id: str,
        query_embedding: List[float],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if not self._initialized:
            await self.initialize()

        if self._dim is not None and len(query_embedding) != int(self._dim):
            raise VectorStoreError(
                message=f"Memory Qdrant dimension mismatch: collection={self._dim} embedder={len(query_embedding)}",
                operation="memory_search",
                details={"collection": self.collection, "collection_dim": self._dim, "embedder_dim": len(query_embedding)},
            )

        mods = _require_qdrant_client()
        Filter = mods["Filter"]
        FieldCondition = mods["FieldCondition"]
        MatchValue = mods["MatchValue"]

        qfilter = Filter(must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))])

        try:
            if hasattr(self._client, "search"):
                hits = self._client.search(
                    collection_name=self.collection,
                    query_vector=query_embedding,
                    limit=int(limit),
                    query_filter=qfilter,
                    with_payload=True,
                )
            else:
                resp = self._client.query_points(
                    collection_name=self.collection,
                    query=query_embedding,
                    limit=int(limit),
                    query_filter=qfilter,
                    with_payload=True,
                )
                hits = getattr(resp, "points", resp)
        except Exception as e:
            raise VectorStoreError(
                message=f"Memory search failed: {e}",
                operation="memory_search",
                details={"collection": self.collection, "workspace_id": workspace_id},
            ) from e

        out: List[Dict[str, Any]] = []
        for h in hits or []:
            payload = dict(getattr(h, "payload", {}) or {})
            score = float(getattr(h, "score", 0.0))
            out.append(
                {
                    "key": payload.get("key"),
                    "score": score,
                    "snippet": payload.get("snippet"),
                    "payload": payload,
                }
            )
        return out
