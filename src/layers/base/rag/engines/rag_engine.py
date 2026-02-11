from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.core.contracts import SearchResult as CoreSearchResult
from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore
from src.layers.base.rag.embedders.query_embedder import QueryEmbedder


class RAGEngine:
    """
    Base search engine:
    - embeds query
    - executes vector search in VectorStore (FAISS)
    """

    def __init__(self):
        cfg = settings.get_vector_store_config()

        # VectorStoreConfig is a typed object (not dict)
        index_path = getattr(cfg, "path", None) or settings.faiss_index_path
        dimension = getattr(cfg, "dimension", None) or settings.faiss_dimension

        self.vector_store = FAISSVectorStore(index_path=str(index_path), dimension=int(dimension))
        self.embedder = QueryEmbedder(provider_type="sentence_transformer")

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

        results = await self.vector_store.search(
            query=query,
            query_embedding=query_vec,
            k=k,
            filter=filters,
            include_metadata=True,
        )

        if similarity_threshold is not None:
            results = [r for r in results if (r.score or 0.0) >= similarity_threshold]

        return results
