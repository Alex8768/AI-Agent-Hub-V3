"""
Search endpoints (vector search via RAGEngine).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult

router = APIRouter(tags=["Search"])


@router.post("/api/v1/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """Search documents using vector search."""
    # NOTE: RAGEngine is not wired in this repo yet.
    # Return a clear status instead of a misleading 500.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Search is not implemented yet",
    )
