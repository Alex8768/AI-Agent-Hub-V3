"""
Hybrid search endpoint: vector search + optional graph augmentation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult
from src.api.dependencies import get_workspace
from src.api.dependencies_impl import get_hybrid_retriever, get_rag_engine
from src.services.search.search_service import SearchService

router = APIRouter(tags=["Search"])


@router.post("/api/v1/search-hybrid")
async def search_documents_hybrid(
    http: Request,
    request: SearchRequest,
    workspace_id: str = Depends(get_workspace),
    engine=Depends(get_rag_engine),
    retriever=Depends(get_hybrid_retriever),
) -> Dict[str, Any]:
    """
    Hybrid retrieval:
    - vector results (same as /api/v1/search)
    - graph augmentation (nodes/edges) if feature_graphrag enabled
    - evidence (source_refs) for UI
    """
    try:
        return await SearchService().search_hybrid(
            http,
            request,
            workspace_id=workspace_id,
            graph_depth=1,
            engine=engine,
            retriever=retriever,
        )
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hybrid search backend unavailable: {str(e)}",
        )
