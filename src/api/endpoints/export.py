"""
Export endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from src.api.schemas import ExportRequest, ExportResult

router = APIRouter(tags=["Export"])


@router.post("/api/v1/export", response_model=ExportResult)
async def export_document(request: ExportRequest):
    """Export content to various formats."""
    # NOTE: ExportManager is not wired in this repo yet.
    # Return a clear status instead of a misleading 500.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Export is not implemented yet",
    )
