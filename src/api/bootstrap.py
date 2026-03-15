"""API bootstrap helpers (lifespan hooks).

Keep src/api/main.py thin: app wiring + router includes.
All startup/shutdown side-effects live here.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.core.config import settings, get_settings
from src.observability.tracing.setup import setup_tracing


async def _init_core_components() -> None:
    from src.core.initializer import initialize_core_components
    await initialize_core_components()


async def _cleanup_core_components() -> None:
    from src.core.initializer import cleanup_core_components
    await cleanup_core_components()


async def _wire_singletons(app: FastAPI) -> None:
    """Wire process-level singletons into app.state (best-effort)."""
    # Base: cache one RAGEngine per process
    try:
        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.core.providers import get_vector_store

        app.state.rag_engine = RAGEngine()
        # Warm up FAISS singleton once per process
        await get_vector_store()
        logger.info("✅ RAGEngine singleton ready (FAISS initialized)")
    except Exception as e:
        logger.warning(f"⚠️ RAGEngine singleton skipped (non-fatal): {e}")

    # Pro: cache HybridRetriever only when Pro flags enabled
    try:
        s = get_settings()
        if (
            (getattr(s, "feature_reasoning_api", False) or getattr(s, "feature_hybrid_search_api", False))
            and getattr(s, "feature_graphrag", False)
        ):
            from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever

            app.state.hybrid_retriever = HybridRetriever()
            logger.info("✅ HybridRetriever singleton ready (Pro)")
    except Exception as e:
        logger.warning(f"⚠️ HybridRetriever singleton skipped (non-fatal): {e}")

    # Workspace MCP runtime (tool registry + local invoker)
    try:
        from src.api.mcp_workspace_runtime import wire_workspace_mcp_runtime

        wire_workspace_mcp_runtime(app)
        logger.info("✅ Workspace MCP runtime wired (list_files/read_file/save_file)")
    except Exception as e:
        logger.warning(f"⚠️ Workspace MCP runtime skipped (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager."""
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"📁 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")

    # Tracing (best-effort, optional deps)
    try:
        setup_tracing(app, service_name="ai-agent-hub")
        logger.info("✅ OpenTelemetry tracing initialized")
    except Exception as e:
        logger.warning(f"⚠️ Tracing initialization skipped (non-fatal): {e}")

    await _init_core_components()
    await _wire_singletons(app)

    yield

    logger.info("👋 Shutting down AI Agent Hub V3...")
    try:
        await asyncio.wait_for(_cleanup_core_components(), timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️ Core cleanup timed out after 10s (non-fatal)")
    except Exception as e:
        logger.warning(f"⚠️ Core cleanup failed (non-fatal): {e}")
