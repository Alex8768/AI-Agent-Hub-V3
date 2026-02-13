"""
Search endpoints (vector search via RAGEngine).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult

router = APIRouter(tags=["Search"])


@router.post("/api/v1/search", response_model=List[SearchResult])
async def search_documents(http: Request, request: SearchRequest):
    """Search documents using vector search."""
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine

        engine = getattr(http.app.state, 'rag_engine', None) or RAGEngine()

        results = await engine.search(
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold,
            workspace_id="default",
        )

        response: List[SearchResult] = []

        for r in results:
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

        return response

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search backend unavailable: {str(e)}",
        )
