from __future__ import annotations

from loguru import logger
from sqlalchemy import text

from src.infrastructure.database.session import get_engine


async def init_db() -> None:
    """
    Safe DB initialization with Alembic migrations.
    Does NOT create tables directly.
    Only warns if alembic_version table is missing.
    """
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            # Check if alembic_version exists (migrations applied)
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            )
            if result.first() is None:
                logger.warning(
                    "⚠️ Database not initialized with migrations. "
                    "Run: alembic upgrade head"
                )
            else:
                logger.info("✅ Database schema is managed by Alembic")
    except Exception as e:
        logger.warning(f"⚠️ DB check failed (non-fatal): {e}")
