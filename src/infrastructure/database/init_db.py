from __future__ import annotations

from loguru import logger

from src.infrastructure.database.session import get_engine
from src.infrastructure.database.base import Base

# Import models so they are registered on Base.metadata
from src.infrastructure.database.models import DocumentRecord  # noqa: F401


async def init_db() -> None:
    """
    Safe DB initialization (dev-friendly).
    Creates tables if they don't exist.
    Must not crash app startup if DB is unavailable.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ DB init: tables ensured")
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped (non-fatal): {e}")
