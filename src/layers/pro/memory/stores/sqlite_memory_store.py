from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.memory_item import MemoryItem


class SQLiteMemoryStore:
    """
    Pro Memory MVP using the existing SQLAlchemy async DB.

    API matches MemoryStore protocol in src/core/providers.py:
    - put(workspace_id, key, value, metadata?)
    - get(workspace_id, key)
    - query(workspace_id, text, limit)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def put(self, *, workspace_id: str, key: str, value: Any, metadata: Optional[dict[str, Any]] = None) -> None:
        # store as plain text for MVP
        val = str(value)
        meta = dict(metadata or {})

        q = select(MemoryItem).where(MemoryItem.workspace_id == workspace_id, MemoryItem.key == key)
        res = await self._db.execute(q)
        row = res.scalar_one_or_none()

        if row is None:
            self._db.add(MemoryItem(workspace_id=workspace_id, key=key, value=val, meta=meta))
        else:
            row.value = val
            row.meta = meta

        await self._db.commit()

    async def get(self, *, workspace_id: str, key: str) -> Optional[Any]:
        q = select(MemoryItem).where(MemoryItem.workspace_id == workspace_id, MemoryItem.key == key)
        res = await self._db.execute(q)
        row = res.scalar_one_or_none()
        return None if row is None else row.value

    async def query(self, *, workspace_id: str, text: str, limit: int = 10) -> list[dict[str, Any]]:
        # Simple LIKE search over value (MVP)
        # Note: For SQLite, LIKE is case-insensitive by default depending on collation.
        pattern = f"%{text}%"
        q = (
            select(MemoryItem)
            .where(MemoryItem.workspace_id == workspace_id, MemoryItem.value.like(pattern))
            .order_by(MemoryItem.id.desc())
            .limit(int(limit))
        )
        res = await self._db.execute(q)
        rows = res.scalars().all()

        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "key": r.key,
                    "value": r.value,
                    "metadata": dict(r.meta or {}),
                    "created_at": getattr(r, "created_at", None),
                    "updated_at": getattr(r, "updated_at", None),
                }
            )
        return out

    async def delete(self, *, workspace_id: str, key: str) -> int:
        q = delete(MemoryItem).where(MemoryItem.workspace_id == workspace_id, MemoryItem.key == key)
        res = await self._db.execute(q)
        await self._db.commit()
        # res.rowcount may be None on some dialects; normalize
        return int(res.rowcount or 0)
