"""
Search endpoints (vector search via RAGEngine).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult
from src.api.dependencies import get_workspace
from src.api.dependencies_impl import get_rag_engine
from src.services.search.search_service import SearchService

router = APIRouter(tags=["Search"])


@router.post("/api/v1/search", response_model=List[SearchResult])
async def search_documents(
    http: Request,
    request: SearchRequest,
    workspace_id: str = Depends(get_workspace),
    engine=Depends(get_rag_engine),
):
    """Search documents using vector search."""
    try:
        return await SearchService().search(http, request, workspace_id=workspace_id, engine=engine)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search backend unavailable: {str(e)}",
        )
