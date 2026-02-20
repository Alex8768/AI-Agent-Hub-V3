"""
Main API for AI Agent Hub V3.
Bootstrap-only: app init, middleware, router wiring, error handlers.
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from src.core.config import settings
from src.api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    RateLimitMiddleware,
)

from src.api.endpoints.health import router as health_router
from src.api.endpoints.llm import router as llm_router
from src.api.endpoints.documents import router as documents_router
from src.api.endpoints.search import router as search_router
from src.api.endpoints.export import router as export_router
from src.api.endpoints.streaming import router as streaming_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"📁 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")

    from src.core.initializer import initialize_core_components
    await initialize_core_components()

    # Base polish: initialize and cache one RAGEngine for the whole app process
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
        app.state.rag_engine = RAGEngine()
        # Warm up FAISS singleton once per process
        await get_vector_store_singleton()
        logger.info("✅ RAGEngine singleton ready (FAISS initialized)")
    except Exception as e:
        logger.warning(f"⚠️ RAGEngine singleton skipped (non-fatal): {e}")


    yield

    logger.info("👋 Shutting down AI Agent Hub V3...")
    from src.core.initializer import cleanup_core_components
    try:
        await asyncio.wait_for(cleanup_core_components(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️ Core cleanup timed out after 10s (non-fatal)")
    except Exception as e:
        logger.warning(f"⚠️ Core cleanup failed (non-fatal): {e}")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Agent Platform - ARCHITECTURE_V3 Implementation",
    version=settings.app_version,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url="/api/v1/redoc" if settings.debug else None,
    openapi_url="/api/v1/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)

if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests=settings.rate_limit_requests,
        period=settings.rate_limit_period,
    )

# Routers
app.include_router(health_router)
app.include_router(llm_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(streaming_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/api/v1/docs" if settings.debug else None,
        "health": "/health",
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": request.url.path, "method": request.method},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "path": request.url.path, "method": request.method},
    )


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug,
    )


if __name__ == "__main__":
    run_server()
