"""
Core lifecycle initialization for AI Agent Hub.

This module is OPTIONAL.
API startup must NOT fail if something here breaks.
"""

from __future__ import annotations

from loguru import logger


async def initialize_core_components() -> None:
    """
    Initialize core subsystems.

    This function should be SAFE:
    - no required external dependencies
    - no hard failures
    """
    logger.info("🔧 Core initializer: start")

    # Safe DB init (dev-friendly)
    from src.infrastructure.database.init_db import init_db
    await init_db()

    # Examples (later):
    # - warm up LLM providers
    # - check vector store connectivity
    # - preload embeddings models
    # - validate config


    # Safe warmup: embeddings model (prevents first-request slowdown)
    try:
        from src.adapters.embedding import get_embedding_factory
        factory = get_embedding_factory()
        await factory.create_embedding_model("sentence_transformer")
        logger.info("✅ Warmup: embeddings ready")
    except Exception as e:
        logger.warning(f"⚠️ Warmup: embeddings skipped (non-fatal): {e}")

    logger.info("✅ Core initializer: done")


async def cleanup_core_components() -> None:
    """
    Cleanup core subsystems on shutdown (best-effort).
    Never raises fatal errors.
    """
    logger.info("🧹 Core cleanup: start")

    # 1) Embedding factory cleanup (shutdown executors / release model refs)
    try:
        from src.adapters.embedding import get_embedding_factory
        factory = get_embedding_factory()
        await factory.cleanup_all()
        logger.info("✅ Cleanup: embedding factory cleaned")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup: embedding factory skipped (non-fatal): {e}")

    # 2) Vector store singleton cleanup (flush + shutdown executor)
    try:
        from src.core.providers import get_vector_store
        store = await get_vector_store()
        try:
            await store.cleanup()
            logger.info("✅ Cleanup: vector store cleaned")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup: vector store cleanup failed (non-fatal): {e}")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup: vector store singleton unavailable (non-fatal): {e}")

    logger.info("👋 Core cleanup: done")

