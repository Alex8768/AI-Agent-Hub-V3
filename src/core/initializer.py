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

    # Examples (later):
    # - warm up LLM providers
    # - check vector store connectivity
    # - preload embeddings models
    # - validate config

    logger.info("✅ Core initializer: done")


async def cleanup_core_components() -> None:
    """
    Cleanup core subsystems on shutdown.
    """
    logger.info("🧹 Core cleanup: start")

    # Examples (later):
    # - close DB connections
    # - flush queues
    # - shutdown background workers

    logger.info("👋 Core cleanup: done")
