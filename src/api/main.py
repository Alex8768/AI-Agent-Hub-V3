"""
Main API for AI Agent Hub V3.
Based on ARCHITECTURE_V3 design.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, Request, Depends, HTTPException, status, File, UploadFile, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
from loguru import logger

from src.core.config import settings
from src.api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    RateLimitMiddleware,
)
from src.api.dependencies import get_current_user, get_workspace
from src.api.schemas import (
    LLMRequest, LLMResponse, SearchRequest, SearchResult,
    ExportRequest, ExportResult, Document, HealthResponse
)

from src.api.endpoints.health import router as health_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"📁 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    
    # Initialize core components
    from src.core.initializer import initialize_core_components
    await initialize_core_components()
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI Agent Hub V3...")
    from src.core.initializer import cleanup_core_components
    await cleanup_core_components()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Agent Platform - ARCHITECTURE_V3 Implementation",
    version=settings.app_version,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url="/api/v1/redoc" if settings.debug else None,
    openapi_url="/api/v1/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Add middleware
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
        period=settings.rate_limit_period
    )

app.include_router(health_router)


# ============ ROOT ENDPOINT ============
# ============ ROOT ENDPOINT ============
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


# ============ LLM ENDPOINTS ============
@app.post("/api/v1/llm/generate", response_model=LLMResponse, tags=["LLM"])
async def generate_completion(request: LLMRequest):
    """Generate text completion using LLM."""
    try:
        from src.layers.base.llm.providers import get_llm_provider
        
        provider = await get_llm_provider(
            provider_type=request.provider or settings.llm_provider
        )
        
        # Build core Message list (system + user)
        from src.core.types import Message, MessageRole

        messages = []
        if request.system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=request.system_prompt))
        messages.append(Message(role=MessageRole.USER, content=request.prompt))

        # Config overrides
        cfg = {}
        if request.temperature is not None:
            cfg["temperature"] = request.temperature
        if request.max_tokens is not None:
            cfg["max_tokens"] = request.max_tokens
        if request.model:
            cfg["model"] = request.model

        completion = await provider.complete(messages=messages, config=cfg or None)

        return LLMResponse(
            content=completion.content,
            model=completion.model,
            provider=completion.provider,
            tokens_used=completion.tokens_used or 0,
            finish_reason=completion.finish_reason,
            metadata=completion.metadata or {}
        )
        
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@app.post("/api/v1/llm/generate-stream", tags=["LLM"])
async def generate_completion_stream(request: LLMRequest):
    """Generate streaming text completion (JSON-SSE)."""
    try:
        import json
        from src.layers.base.llm.providers import get_llm_provider
        from src.core.types import Message, MessageRole

        provider = await get_llm_provider(
            provider_type=request.provider or settings.llm_provider
        )

        async def event_generator():
            # Build core Message list (system + user)
            messages = []
            if request.system_prompt:
                messages.append(Message(role=MessageRole.SYSTEM, content=request.system_prompt))
            messages.append(Message(role=MessageRole.USER, content=request.prompt))

            cfg = {}
            if request.temperature is not None:
                cfg["temperature"] = request.temperature
            if request.max_tokens is not None:
                cfg["max_tokens"] = request.max_tokens
            if request.model:
                cfg["model"] = request.model

            buffer = ""
            min_flush = 40  # characters

            async for chunk in provider.complete_stream(messages=messages, config=cfg or None):
                text = chunk.content or ""
                if not text:
                    continue

                buffer += text

                if len(buffer) >= min_flush or buffer.endswith((".", "!", "?", "\n")):
                    payload = json.dumps({"delta": buffer}, ensure_ascii=False)
                    yield f"event: token\ndata: {payload}\n\n"
                    buffer = ""

            # Final flush
            if buffer:
                payload = json.dumps({"delta": buffer}, ensure_ascii=False)
                yield f"event: token\ndata: {payload}\n\n"

            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"LLM stream generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream generation failed: {str(e)}"
        )


# ============ DOCUMENT ENDPOINTS ============

@app.post("/api/v1/documents/upload", response_model=Document, tags=["Documents"])
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
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@app.get("/api/v1/documents", response_model=List[Document], tags=["Documents"])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List documents."""
    try:
        from src.services.document import document_service
        
        documents = await document_service.list_documents(
            skip=skip,
            limit=limit,
        )
        
        return documents
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


# ============ SEARCH ENDPOINTS ============
@app.post("/api/v1/search", response_model=List[SearchResult], tags=["Search"])
async def search_documents(request: SearchRequest):
    """Search documents using vector search."""
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine
        
        engine = RAGEngine()
        results = await engine.search(
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold,
        )
        
        return [
            SearchResult(
                document_id=r.document_id,
                chunk_id=r.chunk_id,
                content=r.content,
                score=r.score,
                metadata=r.metadata,
                source_document=r.source_document,
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ============ EXPORT ENDPOINTS ============
@app.post("/api/v1/export", response_model=ExportResult, tags=["Export"])
async def export_document(request: ExportRequest):
    """Export content to various formats."""
    try:
        from src.layers.base.export.export_manager import ExportManager
        
        manager = ExportManager()
        result = await manager.export(
            content=request.content,
            format=request.format,
            template=request.template,
            options=request.options,
        )
        
        return ExportResult(
            file_path=result.file_path,
            file_size=result.file_size,
            format=result.format,
            download_url=result.download_url,
            metadata=result.metadata,
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# ============ STREAMING ENDPOINTS ============
@app.get("/api/v1/stream/{session_id}", tags=["Streaming"])
async def stream_events(session_id: str, request: Request):
    """Stream agent events via Server-Sent Events."""
    if not settings.streaming_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is disabled"
        )
    
    try:
        from src.layers.base.streaming.publishers.sse_publisher import SSEPublisher
        
        publisher = SSEPublisher()
        
        async def event_generator():
            queue = await publisher.subscribe(session_id)
            
            try:
                # Send initial event
                yield {
                    "event": "connected",
                    "data": {
                        "session_id": session_id,
                        "message": "Connected to event stream"
                    }
                }
                
                # Stream events
                while True:
                    if await request.is_disconnected():
                        break
                    
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield event
                    except asyncio.TimeoutError:
                        # Send keep-alive
                        yield ": keep-alive\n\n"
                        
            except asyncio.CancelledError:
                pass
            finally:
                await publisher.unsubscribe(session_id, queue)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream connection failed: {str(e)}"
        )


# ============ ERROR HANDLERS ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
            "method": request.method,
        },
    )


# ============ MAIN ENTRY POINT ============
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
