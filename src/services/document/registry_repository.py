from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.infrastructure.database.models import DocumentRecord


class DocumentRegistryRepository:
    async def create(self, db: AsyncSession, record: DocumentRecord) -> DocumentRecord:
        db.add(record)
        try:
            await db.commit()
        except IntegrityError:
            # Another request inserted the same (workspace_id, content_hash) concurrently
            await db.rollback()
            existing = await self.find_by_hash(db, workspace_id=record.workspace_id, content_hash=record.content_hash)
            if existing is not None:
                return existing
            raise
        await db.refresh(record)
        return record



    async def update(self, db: AsyncSession, record: DocumentRecord) -> DocumentRecord:
        await db.commit()
        await db.refresh(record)
        return record



    async def get(self, db: AsyncSession, document_id: str) -> DocumentRecord | None:
        stmt = select(DocumentRecord).where(DocumentRecord.id == document_id)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def delete_record(self, db: AsyncSession, document_id: str) -> bool:
        rec = await self.get(db, document_id)
        if rec is None:
            return False
        await db.delete(rec)
        await db.commit()
        return True

    async def find_by_hash(
        self,
        db: AsyncSession,
        *,
        workspace_id: str,
        content_hash: str,
    ) -> DocumentRecord | None:
        stmt = (
            select(DocumentRecord)
            .where(DocumentRecord.workspace_id == workspace_id)
            .where(DocumentRecord.content_hash == content_hash)
            .order_by(DocumentRecord.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        return res.scalars().first()

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
