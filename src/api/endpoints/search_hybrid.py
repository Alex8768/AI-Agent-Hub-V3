"""
Hybrid search endpoint: vector search + optional graph augmentation.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from src.core.config import get_settings
from src.api.schemas import SearchRequest, SearchResult
from src.api.dependencies import get_workspace
from src.api.dependencies_impl import get_hybrid_retriever, get_rag_engine
from src.services.search.contracts import SearchServiceRequest
from src.services.search.search_service import SearchService

router = APIRouter(tags=["Search"])


def _to_service_request(request: SearchRequest) -> SearchServiceRequest:
    return SearchServiceRequest.model_validate(request.model_dump())


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
    s = get_settings()
    if not getattr(s, "feature_hybrid_search_api", False) or not getattr(s, "feature_graphrag", False):
        raise HTTPException(status_code=404, detail="Not Found")

    try:
        payload = await SearchService().search_hybrid(
            http,
            _to_service_request(request),
            workspace_id=workspace_id,
            graph_depth=1,
            engine=engine,
            retriever=retriever,
        )
        rows = payload.get("results", [])
        payload["results"] = [
            SearchResult.model_validate(row.model_dump() if hasattr(row, "model_dump") else row)
            for row in rows
        ]
        return payload
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hybrid search backend unavailable: {str(e)}",
        )
