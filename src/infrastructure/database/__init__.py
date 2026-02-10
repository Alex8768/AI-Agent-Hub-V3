"""
Database infrastructure (Base layer).

FastAPI dependency: get_db() -> AsyncSession via async context manager.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_sessionmaker


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        yield session
