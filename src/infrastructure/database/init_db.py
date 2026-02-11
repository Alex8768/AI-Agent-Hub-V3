from __future__ import annotations

from loguru import logger
from sqlalchemy import text

from src.infrastructure.database.session import get_engine
from src.infrastructure.database.base import Base

# Import models so they are registered on Base.metadata
from src.infrastructure.database.models import DocumentRecord  # noqa: F401


async def _repair_documents_table_if_needed() -> None:
    """
    Dev-only safety net: SQLite has no automatic schema migrations.
    If documents table exists but misses required columns, drop & recreate it.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        # Does table exist?
        exists = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        )
        if exists.first() is None:
            return

        cols = await conn.execute(text("PRAGMA table_info(documents)"))
        col_names = {row[1] for row in cols.fetchall()}  # row[1] = name

        required = {"workspace_id", "storage_key", "content_hash", "status", "size_bytes"}
        if not required.issubset(col_names):
            logger.warning(f"⚠️ DB repair: dropping stale 'documents' table (cols={sorted(col_names)})")
            await conn.execute(text("DROP TABLE documents"))


async def init_db() -> None:
    """
    Safe DB initialization (dev-friendly).
    Creates tables if they don't exist.
    Must not crash app startup if DB is unavailable.
    """
    try:
        await _repair_documents_table_if_needed()

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ DB init: tables ensured")
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped (non-fatal): {e}")
