from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import DocumentRecord
from src.infrastructure.storage.local_storage import LocalStorage
from src.services.document.registry_repository import DocumentRegistryRepository


class DocumentService:
    def __init__(self):
        self.repo = DocumentRegistryRepository()
        self.storage = LocalStorage()

    def _hash_bytes(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    async def create_from_upload(
        self,
        db: AsyncSession,
        *,
        filename: str,
        data: bytes,
        workspace_id: str = "default",
        mime: str | None = None,
    ) -> DocumentRecord:
        doc_id = uuid4().hex
        content_hash = self._hash_bytes(data)

        stored = self.storage.save_upload(
            workspace_id=workspace_id,
            doc_id=doc_id,
            filename=filename,
            data=data,
        )

        now = datetime.utcnow()
        record = DocumentRecord(
            id=doc_id,
            workspace_id=workspace_id,
            filename=filename,
            content_hash=content_hash,
            mime=mime,
            size_bytes=stored.size_bytes,
            status="completed",  # Этап 1.2: registry-only. Ingest wiring -> 1.3
            storage_key=stored.storage_key,
            created_at=now,
            updated_at=now,
        )
        return await self.repo.create(db, record)

    async def list_documents(
        self,
        db: AsyncSession,
        *,
        skip: int,
        limit: int,
        status: str | None = None,
        workspace_id: str | None = None,
    ):
        return await self.repo.list(db, skip=skip, limit=limit, status=status, workspace_id=workspace_id)
