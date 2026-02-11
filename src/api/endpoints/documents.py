"""
Documents endpoints.
Upload -> ingest pipeline; list -> document service.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from loguru import logger

from src.core.config import settings
from src.api.schemas import Document

router = APIRouter(tags=["Documents"])


@router.post("/api/v1/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(default=settings.ingest_chunk_size, ge=100, le=10000),
    chunk_overlap: int = Query(default=settings.ingest_chunk_overlap, ge=0, le=1000),
):
    """Upload and process a document."""
    try:
        from src.layers.base.ingest.pipelines.ingest_pipeline import IngestPipeline

        # Save uploaded file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Process document
            pipeline = IngestPipeline()
            result = await pipeline.process(
                file_path=tmp_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            return Document(
                id=result.document_id,
                name=file.filename,
                path=tmp_path,
                format=result.format,
                size=len(content),
                status=result.status,
                chunks=result.chunks,
                metadata=result.metadata,
            )

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/api/v1/documents", response_model=List[Document])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List documents."""
    # NOTE: Document listing storage is not wired yet in this repo.
    # We return a clear status instead of a misleading 500.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document listing is not implemented yet",
    )
