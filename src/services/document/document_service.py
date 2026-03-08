from __future__ import annotations

import hashlib
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.core.config import settings
from src.infrastructure.database.models import DocumentRecord
from src.infrastructure.storage.local_storage import LocalStorage
from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
from src.layers.pro.graph_rag.jobs.service import get_entity_extraction_jobs_service
from src.services.document.registry_repository import DocumentRegistryRepository
from src.services.document.ingest_service import IngestService


class DocumentService:
    def __init__(self, *, extraction_jobs_service=None):
        self.repo = DocumentRegistryRepository()
        self.storage = LocalStorage()
        self._extraction_jobs_service = extraction_jobs_service

    def _hash_bytes(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _bytes_to_text(self, data: bytes) -> str:
        # Base: handle text-ish uploads. (pdf/docx parsing later)
        return data.decode("utf-8", errors="ignore")

    async def _get_vector_store(self):
        return await get_vector_store_singleton()

    def _get_extraction_jobs_service(self):
        return self._extraction_jobs_service or get_entity_extraction_jobs_service()

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

        # 1) Fast dedup: if already ingested successfully, return immediately (no storage IO)
        existing = await self.repo.find_by_hash(db, workspace_id=workspace_id, content_hash=content_hash)
        if existing is not None and existing.status != "error":
            return existing

        # 2) If there is an error record, wipe it deterministically (DB + storage best-effort)
        if existing is not None and existing.status == "error":
            try:
                if getattr(existing, "storage_key", None):
                    await self.storage.delete(existing.storage_key)
            except Exception:
                pass
            try:
                await self.repo.delete_record(db, existing.id)
            except Exception:
                pass

        # 3) Save upload first, but ALWAYS compensate if DB insert dedups concurrently
        stored = await self.storage.save_upload(
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

        # If create() deduped due to concurrent insert, it returns the existing record.
        # In that case, delete the file we just saved to avoid orphan storage.
        if record.id != doc_id:
            try:
                await self.storage.delete(stored.storage_key)
            except Exception:
                pass
            # If existing is good, return it; if it's error, caller can retry later.
            return record

        # 4) Ingest + index (only for the winner that actually created the record)
        try:
            text = self._bytes_to_text(data)

            vector_store = await self._get_vector_store()
            ingest_start = perf_counter()
            stats_before = await vector_store.get_stats()
            vectors_before = stats_before.get('total_vectors') or stats_before.get('total_vectors', 0)

            ingest = IngestService(
                vector_store=vector_store,
                embedding_model=None,  # будет внедряться позже через DI
                chunk_size=chunk_size or settings.ingest_chunk_size,
                chunk_overlap=chunk_overlap or settings.ingest_chunk_overlap,
            )

            result = await ingest.ingest_text(
                text=text,
                filename=filename,
                metadata={"workspace_id": workspace_id},
                document_id=record.id,
            )

            stats_after = await vector_store.get_stats()
            vectors_after = stats_after.get('total_vectors') or stats_after.get('total_vectors', 0)
            ingest_ms = int((perf_counter() - ingest_start) * 1000)
            logger.info(
                'Ingest completed',
                extra={
                    'document_id': record.id,
                    'filename': filename,
                    'chunks': getattr(result, 'total_chunks', None),
                    'ingest_ms': ingest_ms,
                    'faiss_vectors_before': vectors_before,
                    'faiss_vectors_after': vectors_after,
                    'faiss_vectors_delta': (vectors_after - vectors_before),
                },
            )

            if result.success:
                record.status = "completed"
                record.chunks_count = result.total_chunks
                record.indexed_at = datetime.utcnow()
                record.error_message = None
                # A1.3: managed best-effort background extraction job for graph entities.
                try:
                    jobs = self._get_extraction_jobs_service()
                    job = await jobs.start_document_job(workspace_id=workspace_id, document_id=record.id)
                    logger.info(
                        "Entity extraction job started",
                        extra={
                            "document_id": record.id,
                            "workspace_id": workspace_id,
                            "job_id": job.job_id,
                            "chunks_total": job.total_chunks,
                        },
                    )
                except Exception as e:
                    # Extraction is additive for GraphRAG; ingest success must not be rolled back.
                    logger.warning(
                        "Entity extraction job was not started",
                        extra={
                            "document_id": record.id,
                            "workspace_id": workspace_id,
                            "reason": str(e),
                        },
                    )
            else:
                record.status = "error"
                record.error_message = "; ".join(result.errors)[:1000]

        except Exception as e:
            record.status = "error"
            record.error_message = str(e)[:1000]

        record.updated_at = datetime.utcnow()
        await self.repo.update(db, record)
        return record

    def get_latest_extraction_job(self, *, workspace_id: str, document_id: str):
        jobs = self._get_extraction_jobs_service()
        return jobs.get_latest_document_job(workspace_id=workspace_id, document_id=document_id)

    def get_extraction_job(self, *, job_id: str):
        jobs = self._get_extraction_jobs_service()
        return jobs.get_job(job_id)






    async def delete_document(self, db: AsyncSession, *, document_id: str) -> bool:
        # 1) Load record
        rec = await self.repo.get(db, document_id)
        if rec is None:
            return False

        # 2) Delete vectors (all chunks with metadata.document_id == document_id)
        try:
            vector_store = await self._get_vector_store()
            # Find chunk IDs in FAISS document store
            chunk_ids = []
            for vid, vdoc in getattr(vector_store, "_document_store", {}).items():
                meta = getattr(vdoc, "metadata", {}) or {}
                if meta.get("document_id") == document_id:
                    chunk_ids.append(vid)
            if chunk_ids:
                await vector_store.delete(chunk_ids)
        except Exception:
            # Non-fatal: DB/storage deletion still proceeds
            pass

        # 3) Delete file
        try:
            await self.storage.delete(rec.storage_key)
        except Exception:
            pass

        # 4) Delete DB row
        return await self.repo.delete_record(db, document_id)


    async def get_document(self, db: AsyncSession, *, document_id: str) -> DocumentRecord | None:
        return await self.repo.get(db, document_id)

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
