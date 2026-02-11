"""
Documents endpoints.
Upload -> ingest pipeline; list -> document service.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from loguru import logger

from src.core.config import settings
from src.api.schemas import DocumentOut, DocumentDetailOut

router = APIRouter(tags=["Documents"])


@router.post("/api/v1/documents/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(default=settings.ingest_chunk_size, ge=100, le=10000),
    chunk_overlap: int = Query(default=settings.ingest_chunk_overlap, ge=0, le=1000),
):
    """Upload document into registry + storage (Base)."""
    # NOTE: chunk_size/chunk_overlap will be used in ingest stage (1.3)
    try:
        from src.infrastructure.database import get_db
        from src.services.document.document_service import DocumentService

        content = await file.read()
        svc = DocumentService()

        async with get_db() as db:
            rec = await svc.create_from_upload(
                db,
                filename=file.filename,
                data=content,
                workspace_id="default",
                mime=getattr(file, "content_type", None),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        return DocumentOut(
            id=rec.id,
            filename=rec.filename,
            size_bytes=rec.size_bytes,
            status=rec.status,
            workspace_id=rec.workspace_id,
            metadata={"chunks_count": rec.chunks_count, "indexed_at": str(rec.indexed_at) if rec.indexed_at else None},
        )

    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )




@router.delete("/api/v1/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Delete document (DB + storage + vectors)."""
    try:
        from src.infrastructure.database import get_db
        from src.services.document.document_service import DocumentService

        svc = DocumentService()
        async with get_db() as db:
            ok = await svc.delete_document(db, document_id=document_id)

        if not ok:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"status": "deleted", "document_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )




@router.get("/api/v1/documents/{document_id}", response_model=DocumentDetailOut, tags=["Documents"])
async def get_document(document_id: str):
    """Get document details by id."""
    try:
        from src.infrastructure.database import get_db
        from src.services.document.document_service import DocumentService

        svc = DocumentService()
        async with get_db() as db:
            rec = await svc.get_document(db, document_id=document_id)

        if rec is None:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentDetailOut(
            id=rec.id,
            filename=rec.filename,
            size_bytes=rec.size_bytes,
            mime=rec.mime,
            status=rec.status,
            workspace_id=rec.workspace_id,
            chunks_count=rec.chunks_count,
            indexed_at=str(rec.indexed_at) if rec.indexed_at else None,
            error_message=rec.error_message,
            metadata={},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.get("/api/v1/documents", response_model=List[DocumentOut])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List documents from registry."""
    try:
        from src.infrastructure.database import get_db
        from src.services.document.document_service import DocumentService

        svc = DocumentService()
        async with get_db() as db:
            rows = await svc.list_documents(db, skip=skip, limit=limit, workspace_id="default")

        return [
            DocumentOut(
                id=r.id,
                filename=r.filename,
                size_bytes=r.size_bytes,
                status=r.status,
                workspace_id=r.workspace_id,
                metadata={},
            )
            for r in rows
        ]

    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )
