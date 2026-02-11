"""
Export endpoints.
POST /api/v1/export -> creates an artifact and returns metadata
GET  /api/v1/export/{export_id}/download -> downloads artifact
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from loguru import logger

from src.api.schemas import ExportRequest, ExportResult

router = APIRouter(tags=["Export"])


@router.post("/api/v1/export", response_model=ExportResult)
async def export_document(request: ExportRequest):
    """Export content to various formats."""
    try:
        from src.infrastructure.database import get_db
        from src.layers.base.export.export_manager import ExportManager

        async with get_db() as db:
            mgr = ExportManager()
            artifact = await mgr.export(
                db,
                format=request.format,
                content=request.content,
                document_id=request.document_id,
            )

        # Put download_url into metadata to avoid schema changes
        return ExportResult(
            format=artifact.format,
            output_path=artifact.output_path,
            bytes_base64=None,
            metadata={
                "export_id": artifact.export_id,
                "size_bytes": artifact.size_bytes,
                "download_url": artifact.download_url,
            },
        )

    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Export backend unavailable: {str(e)}",
        )


@router.get("/api/v1/export/{export_id}/download")
async def download_export(export_id: str):
    """Download an exported artifact by export_id."""
    try:
        from src.layers.base.export.export_manager import ExportManager

        mgr = ExportManager()
        f = mgr.find_export_file(export_id)
        if not f:
            raise HTTPException(status_code=404, detail="Export not found")

        return FileResponse(
            path=str(f),
            filename=f.name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}",
        )
