from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.infrastructure.database.models import DocumentRecord
from src.infrastructure.storage.local_storage import LocalStorage
from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore
from src.services.document.registry_repository import DocumentRegistryRepository
from src.services.document.ingest_service import IngestService


class DocumentService:
    def __init__(self):
        self.repo = DocumentRegistryRepository()
        self.storage = LocalStorage()

    def _hash_bytes(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _bytes_to_text(self, data: bytes) -> str:
        # Base: handle text-ish uploads. (pdf/docx parsing later)
        return data.decode("utf-8", errors="ignore")

    async def _get_vector_store(self) -> FAISSVectorStore:
        cfg = settings.get_vector_store_config()
        index_path = getattr(cfg, "path", None) or settings.faiss_index_path
        dimension = getattr(cfg, "dimension", None) or settings.faiss_dimension
        store = FAISSVectorStore(index_path=str(index_path), dimension=int(dimension))
        await store.initialize()
        return store

    async def create_from_upload(
        self,
        db: AsyncSession,
        *,
        filename: str,
        data: bytes,
        workspace_id: str = "default",
        mime: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
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
            status="processing",
            storage_key=stored.storage_key,
            created_at=now,
            updated_at=now,
        )
        record = await self.repo.create(db, record)

        # Ingest + index
        try:
            text = self._bytes_to_text(data)

            vector_store = await self._get_vector_store()
            ingest = IngestService(
                chunk_size=chunk_size or settings.ingest_chunk_size,
                chunk_overlap=chunk_overlap or settings.ingest_chunk_overlap,
                vector_store=vector_store,
            )

            result = await ingest.ingest_text(
                text=text,
                filename=filename,
                metadata={"workspace_id": workspace_id},
                document_id=record.id,
            )

            if result.success:
                record.status = "completed"
                record.chunks_count = result.total_chunks
                record.indexed_at = datetime.utcnow()
                record.error_message = None
            else:
                record.status = "error"
                record.error_message = "; ".join(result.errors)[:1000]

        except Exception as e:
            record.status = "error"
            record.error_message = str(e)[:1000]

        record.updated_at = datetime.utcnow()
        await self.repo.update(db, record)
        return record

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
