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
        exists = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        )
        if exists.first() is None:
            return

        cols = await conn.execute(text("PRAGMA table_info(documents)"))
        col_names = {row[1] for row in cols.fetchall()}

        required = {"workspace_id", "storage_key", "content_hash", "status", "size_bytes"}
        if not required.issubset(col_names):
            logger.warning(f"⚠️ DB repair: dropping stale 'documents' table (cols={sorted(col_names)})")
            await conn.execute(text("DROP TABLE documents"))


async def _dedupe_documents_rows(conn) -> None:
    """
    Remove duplicates (SQLite-only) so we can apply UNIQUE(workspace_id, content_hash).
    Keeps the oldest row (MIN(rowid)) per key.
    """
    await conn.execute(text("""
        DELETE FROM documents
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM documents
            GROUP BY workspace_id, content_hash
        )
    """))


async def init_db() -> None:
    """
    Safe DB initialization (dev-friendly).
    Creates tables if they don't exist.
    Must not crash app startup if DB is unavailable.
    Also enforces UNIQUE(workspace_id, content_hash) idempotency constraint.
    """
    try:
        await _repair_documents_table_if_needed()

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # Enforce idempotency constraint.
            # SQLite: we can dedupe using rowid to allow creating a unique index.
            # Non-SQLite (e.g., Postgres): rowid doesn't exist; schema should be handled via migrations.
            dialect = conn.dialect.name if hasattr(conn, "dialect") else ""
            if dialect == "sqlite":
                # ensure we can create unique index
                await _dedupe_documents_rows(conn)

                await conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_ws_hash "
                    "ON documents(workspace_id, content_hash)"
                ))
            else:
                logger.info(f"DB init: skipping SQLite rowid dedupe for dialect={dialect}")

        logger.info("✅ DB init: tables ensured")
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped (non-fatal): {e}")
