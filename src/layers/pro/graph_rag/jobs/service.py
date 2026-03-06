from __future__ import annotations

from threading import RLock
from typing import Any

from src.core.config import settings
from src.core.exceptions import ValidationError
from src.core.contracts import VectorDocument
from src.layers.base.rag.vector_stores.factory import get_vector_store_singleton
from src.layers.pro.graph_rag.jobs.registry import EntityExtractionJob
from src.layers.pro.graph_rag.jobs.runner import EntityExtractionJobRunner, ExtractionChunkInput


class EntityExtractionJobsService:
    """Orchestrates entity extraction jobs for a document."""

    def __init__(
        self,
        *,
        runner: EntityExtractionJobRunner | None = None,
        vector_store: Any | None = None,
    ) -> None:
        self._runner = runner or EntityExtractionJobRunner()
        self._vector_store = vector_store

    async def start_document_job(self, *, workspace_id: str, document_id: str) -> EntityExtractionJob:
        if not bool(settings.feature_graphrag):
            raise ValidationError(
                message="GraphRAG feature is disabled",
                field="feature_graphrag",
                value=False,
            )

        store = self._vector_store
        if store is None:
            store = await get_vector_store_singleton()

        chunks = self._collect_document_chunks(
            store=store,
            workspace_id=workspace_id,
            document_id=document_id,
        )
        if not chunks:
            raise ValidationError(
                message="No chunks found for document",
                field="document_id",
                value=document_id,
            )

        return self._runner.start_job(
            workspace_id=workspace_id,
            document_id=document_id,
            chunks=chunks,
        )

    def get_job(self, job_id: str) -> EntityExtractionJob | None:
        return self._runner.get_job(job_id)

    def get_latest_document_job(self, *, workspace_id: str, document_id: str) -> EntityExtractionJob | None:
        return self._runner.get_latest_document_job(workspace_id=workspace_id, document_id=document_id)

    @staticmethod
    def _collect_document_chunks(
        *,
        store: Any,
        workspace_id: str,
        document_id: str,
    ) -> list[ExtractionChunkInput]:
        doc_store = getattr(store, "_document_store", None)
        if not isinstance(doc_store, dict):
            return []

        result: list[ExtractionChunkInput] = []
        for chunk_id, doc in doc_store.items():
            if not isinstance(doc, VectorDocument):
                continue
            meta = (doc.metadata or {}) if isinstance(doc.metadata, dict) else {}
            if str(meta.get("document_id", "")) != str(document_id):
                continue
            if str(meta.get("workspace_id", "default")) != str(workspace_id):
                continue
            if bool(meta.get("_deleted", False)):
                continue

            text = str(getattr(doc, "content", "") or "").strip()
            if not text:
                continue

            result.append(ExtractionChunkInput(chunk_id=str(chunk_id), text=text))

        result.sort(key=lambda x: x.chunk_id)
        return result


_jobs_service_lock = RLock()
_jobs_service_singleton: EntityExtractionJobsService | None = None


def get_entity_extraction_jobs_service() -> EntityExtractionJobsService:
    global _jobs_service_singleton
    if _jobs_service_singleton is not None:
        return _jobs_service_singleton
    with _jobs_service_lock:
        if _jobs_service_singleton is None:
            _jobs_service_singleton = EntityExtractionJobsService()
        return _jobs_service_singleton
