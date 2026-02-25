from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.contracts import VectorDocument, SearchResult
from src.core.exceptions import VectorStoreError


def _preview(text: str | None, max_chars: int = 512) -> str:
    if not text:
        return ""
    return text if len(text) <= max_chars else text[:max_chars]


def _require_qdrant_client() -> Any:
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.models import (  # type: ignore
            Distance,
            VectorParams,
            PointStruct,
            Filter,
            FieldCondition,
            MatchValue,
            PayloadSchemaType,
        )
        return {
            "QdrantClient": QdrantClient,
            "Distance": Distance,
            "VectorParams": VectorParams,
            "PointStruct": PointStruct,
            "Filter": Filter,
            "FieldCondition": FieldCondition,
            "MatchValue": MatchValue,
            "PayloadSchemaType": PayloadSchemaType,
        }
    except Exception as e:
        raise VectorStoreError(
            message="Qdrant client is not installed. Install Pro extras to enable Qdrant.",
            operation="initialize",
            details={"error": str(e)},
        ) from e


@dataclass
class QdrantVectorStore:
    host: str
    port: int
    collection: str
    timeout: int = 10
    name: str = "qdrant"

    _client: Any = None
    _initialized: bool = False
    _dim: Optional[int] = None

    async def initialize(self) -> None:
        if self._initialized:
            return

        mods = _require_qdrant_client()
        QdrantClient = mods["QdrantClient"]

        # Connect
        self._client = QdrantClient(host=self.host, port=self.port, timeout=self.timeout)

        # NOTE: We create collection lazily on first add_documents() when we know vector dim.
        self._initialized = True

    async def cleanup(self) -> None:
        # Nothing special for HTTP client. Keep method for contract symmetry.
        return None

    async def health_check(self) -> Dict[str, Any]:
        try:
            if not self._initialized:
                await self.initialize()
            # lightweight ping
            _ = self._client.get_collections()
            return {"status": "healthy", "provider": "qdrant", "host": self.host, "port": self.port, "collection": self.collection}
        except Exception as e:
            return {"status": "unhealthy", "provider": "qdrant", "error": str(e), "collection": self.collection}

    async def _ensure_collection(self, dim: int) -> None:
        mods = _require_qdrant_client()
        Distance = mods["Distance"]
        VectorParams = mods["VectorParams"]
        PayloadSchemaType = mods["PayloadSchemaType"]

        # Create if missing, validate dim if exists
        try:
            info = self._client.get_collection(self.collection)
            # If existing, ensure dim matches
            try:
                existing_dim = int(info.config.params.vectors.size)  # type: ignore[attr-defined]
                if existing_dim != dim:
                    raise VectorStoreError(
                        message=f"Qdrant dimension mismatch: collection={existing_dim} embedder={dim}",
                        operation="initialize",
                        details={"collection": self.collection, "collection_dim": existing_dim, "embedder_dim": dim},
                    )
            except Exception:
                # If API shape differs, we don't hard fail; we'll just proceed.
                pass
        except Exception:
            # Not found or error -> create
            self._client.recreate_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=int(dim), distance=Distance.COSINE),
            )
            # Optional payload schema hints (safe if supported)
            try:
                self._client.create_payload_index(self.collection, field_name="workspace_id", field_schema=PayloadSchemaType.KEYWORD)
            except Exception:
                pass

        self._dim = dim

    async def add_documents(
        self,
        documents: List[VectorDocument],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        if not self._initialized:
            await self.initialize()

        if not documents:
            return []

        if embeddings is None:
            raise VectorStoreError(
                message="Embeddings are required for add_documents()",
                operation="add_documents",
                details={"documents_count": len(documents)},
            )

        if len(embeddings) != len(documents):
            raise VectorStoreError(
                message="Embeddings count mismatch",
                operation="add_documents",
                details={"documents_count": len(documents), "embeddings_count": len(embeddings)},
            )

        dim = len(embeddings[0]) if embeddings else 0
        if dim <= 0:
            raise VectorStoreError(
                message="Invalid embedding dimension",
                operation="add_documents",
                details={"dimension": dim},
            )

        # Ensure all embeddings have same dim
        for emb in embeddings:
            if len(emb) != dim:
                raise VectorStoreError(
                    message="Embedding dimension mismatch within batch",
                    operation="add_documents",
                    details={"expected": dim, "got": len(emb)},
                )

        await self._ensure_collection(dim)

        mods = _require_qdrant_client()
        PointStruct = mods["PointStruct"]

        points = []
        for doc, emb in zip(documents, embeddings):
            payload = dict(getattr(doc, "metadata", {}) or {})
            payload.setdefault("document_id", doc.id)
            payload.setdefault("workspace_id", payload.get("workspace_id", "default"))
            payload["content_preview"] = _preview(getattr(doc, "content", None))
            points.append(PointStruct(id=doc.id, vector=emb, payload=payload))

        try:
            self._client.upsert(collection_name=self.collection, points=points)
            return [d.id for d in documents]
        except Exception as e:
            raise VectorStoreError(
                message=f"Ошибка добавления документов: {str(e)}",
                operation="add_documents",
                details={"documents_count": len(documents), "collection": self.collection},
            ) from e

    async def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[SearchResult]:
        if not self._initialized:
            await self.initialize()

        if query_embedding is None:
            raise VectorStoreError(
                message="query_embedding is required for search()",
                operation="search",
                details={"query_preview": (query[:80] if query else "")},
            )

        if k <= 0:
            return []

        if self._dim is not None and len(query_embedding) != int(self._dim):
            raise VectorStoreError(
                message=f"Qdrant dimension mismatch: collection={self._dim} embedder={len(query_embedding)}",
                operation="search",
                details={"collection": self.collection, "collection_dim": self._dim, "embedder_dim": len(query_embedding)},
            )

        mods = _require_qdrant_client()
        Filter = mods["Filter"]
        FieldCondition = mods["FieldCondition"]
        MatchValue = mods["MatchValue"]

        qfilter = None
        if filter:
            must = []
            for key, val in filter.items():
                must.append(FieldCondition(key=key, match=MatchValue(value=val)))
            qfilter = Filter(must=must)

        try:
            hits = self._client.search(
                collection_name=self.collection,
                query_vector=query_embedding,
                limit=int(k),
                query_filter=qfilter,
                with_payload=True,
            )
        except Exception as e:
            raise VectorStoreError(
                message=f"Ошибка поиска: {str(e)}",
                operation="search",
                details={"collection": self.collection, "k": int(k)},
            ) from e

        results: List[SearchResult] = []
        for h in hits or []:
            payload = dict(getattr(h, "payload", {}) or {})
            doc = VectorDocument(
                id=str(getattr(h, "id", "")),
                content=str(payload.get("content_preview", "")),
                metadata=payload if include_metadata else {},
                embedding=None,
            )
            score = float(getattr(h, "score", 0.0))
            results.append(SearchResult(document=doc, score=score, distance=float(1.0 - score)))

        return results

    async def delete(self, document_ids: List[str]) -> int:
        if not self._initialized:
            await self.initialize()

        if not document_ids:
            return 0

        try:
            # qdrant_client supports deleting by ids directly
            self._client.delete(collection_name=self.collection, points_selector=document_ids)
            return len(document_ids)
        except Exception as e:
            raise VectorStoreError(
                message=f"Ошибка удаления документов: {str(e)}",
                operation="delete",
                details={"collection": self.collection, "count": len(document_ids)},
            ) from e

    async def delete_documents(self, ids: List[str]) -> int:
        # Alias used by rollback logic
        return await self.delete(ids)

    async def get_stats(self) -> Dict[str, Any]:
        try:
            if not self._initialized:
                await self.initialize()
            try:
                cnt = self._client.count(collection_name=self.collection, exact=True).count
            except Exception:
                cnt = None
            return {
                "provider": "qdrant",
                "collection": self.collection,
                "host": self.host,
                "port": self.port,
                "initialized": self._initialized,
                "dimension": self._dim,
                "points_count": cnt,
            }
        except Exception as e:
            return {"provider": "qdrant", "collection": self.collection, "status": "unhealthy", "error": str(e)}
