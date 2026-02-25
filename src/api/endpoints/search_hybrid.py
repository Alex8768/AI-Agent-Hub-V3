"""
Hybrid search endpoint: vector search + optional graph augmentation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult
from src.api.dependencies import get_workspace

router = APIRouter(tags=["Search"])


@router.post("/api/v1/search-hybrid")
async def search_documents_hybrid(http: Request, request: SearchRequest, workspace_id: str = Depends(get_workspace)) -> Dict[str, Any]:
    """
    Hybrid retrieval:
    - vector results (same as /api/v1/search)
    - graph augmentation (nodes/edges) if feature_graphrag enabled
    - evidence (source_refs) for UI
    """
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever

        engine = getattr(http.app.state, "rag_engine", None) or RAGEngine()

        retriever = HybridRetriever()
        out = await retriever.retrieve(
            engine=engine,
            workspace_id=workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold,
            graph_depth=1,
        )

        # Format vector results into existing SearchResult schema
        response: List[SearchResult] = []
        for r in out.vector_results:
            if not getattr(r, "document", None):
                continue
            doc = r.document
            content = getattr(doc, "content", "") or ""
            metadata = getattr(doc, "metadata", {}) or {}
            snippet = content[: request.snippet_len]

            response.append(
                SearchResult(
                    document_id=metadata.get("document_id", ""),
                    chunk_id=getattr(doc, "id", ""),
                    score=float(getattr(r, "score", 0.0) or 0.0),
                    snippet=snippet,
                    content=content if request.include_content else None,
                    source_document=metadata.get("filename"),
                    metadata=(metadata if request.include_metadata else {}),
                )
            )

        return {
            "results": response,
            "graph": out.graph,
            "evidence": out.evidence,
        }

    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hybrid search backend unavailable: {str(e)}",
        )
