from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.core.contracts import SearchResult as CoreSearchResult
from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
from src.layers.base.rag.embedders.query_embedder import QueryEmbedder

if TYPE_CHECKING:
    from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore


class RAGEngine:
    """
    Base search engine:
    - embeds query
    - executes vector search in VectorStore (FAISS)
    """

    def __init__(self):
        self._vector_store: Optional["FAISSVectorStore"] = None
        self.embedder = QueryEmbedder(provider_type="sentence_transformer")

    async def _get_vector_store(self) -> "FAISSVectorStore":
        if self._vector_store is None:
            self._vector_store = await get_vector_store_singleton()
        return self._vector_store

    async def search(
        self,
        *,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None,
        workspace_id: str = "default",
    ) -> List[CoreSearchResult]:
        filters = dict(filters or {})
        filters.setdefault("workspace_id", workspace_id)

        query_vec = await self.embedder.embed_query(query)

        results = await (await self._get_vector_store()).search(
            query=query,
            query_embedding=query_vec,
            k=k,
            filter=filters,
            include_metadata=True,
        )

        if similarity_threshold is not None:
            results = [r for r in results if (r.score or 0.0) >= similarity_threshold]

        return results
