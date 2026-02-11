"""
Health endpoints.
Kept thin and deterministic.
"""

from __future__ import annotations

import datetime
from fastapi import APIRouter

from src.core.config import settings
from src.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {
        "api": "healthy",
        "environment": settings.environment,
    }

    # Check database if configured
    try:
        from src.infrastructure.database import get_db
        async with get_db() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as e:
        services["database"] = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        services=services,
    )


@router.get("/api/v1/health", include_in_schema=False)
async def api_health_check():
    """API health check."""
    return await health_check()
