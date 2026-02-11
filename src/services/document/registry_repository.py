from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import DocumentRecord


class DocumentRegistryRepository:
    async def create(self, db: AsyncSession, record: DocumentRecord) -> DocumentRecord:
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record



    async def update(self, db: AsyncSession, record: DocumentRecord) -> DocumentRecord:
        await db.commit()
        await db.refresh(record)
        return record

    async def list(
        self,
        db: AsyncSession,
        *,
        skip: int,
        limit: int,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> Sequence[DocumentRecord]:
        stmt = select(DocumentRecord)

        if workspace_id:
            stmt = stmt.where(DocumentRecord.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(DocumentRecord.status == status)

        stmt = stmt.order_by(DocumentRecord.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()
