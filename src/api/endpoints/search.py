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
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine

        engine = RAGEngine()
        results = await engine.search(
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=getattr(request, "similarity_threshold", None),
            workspace_id="default",
        )

        return [
            SearchResult(
                document_id=(r.document.metadata.get("document_id", "") if getattr(r, "document", None) and getattr(r.document, "metadata", None) else ""),
                chunk_id=(r.document.id if getattr(r, "document", None) else ""),
                content=(r.document.content if getattr(r, "document", None) else ""),
                score=getattr(r, "score", 0.0),
                metadata=(r.document.metadata if getattr(r, "document", None) and getattr(r.document, "metadata", None) else {}),
                source_document=(r.document.metadata.get("filename") if getattr(r, "document", None) and getattr(r.document, "metadata", None) else None),
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search backend unavailable: {str(e)}",
        )
