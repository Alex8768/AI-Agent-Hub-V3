from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.services.document.document_service import DocumentService


@dataclass
class _StoredFile:
    storage_key: str
    size_bytes: int


@dataclass
class _FakeRecord:
    id: str
    workspace_id: str
    filename: str
    content_hash: str
    mime: str | None
    size_bytes: int
    status: str
    storage_key: str
    created_at: datetime
    updated_at: datetime
    chunks_count: int | None = None
    indexed_at: datetime | None = None
    error_message: str | None = None


class _FakeRepo:
    def __init__(self) -> None:
        self.updated: _FakeRecord | None = None

    async def find_by_hash(self, db, *, workspace_id: str, content_hash: str):
        return None

    async def create(self, db, record: _FakeRecord) -> _FakeRecord:
        return record

    async def update(self, db, record: _FakeRecord) -> None:
        self.updated = record


class _FakeStorage:
    async def save_upload(self, *, workspace_id: str, doc_id: str, filename: str, data: bytes) -> _StoredFile:
        return _StoredFile(storage_key=f"{workspace_id}/{doc_id}/{filename}", size_bytes=len(data))

    async def delete(self, storage_key: str) -> None:
        return None


class _FakeVectorStore:
    async def get_stats(self):
        return {"total_vectors": 0}


class _JobsWithLookup:
    async def start_document_job(self, *, workspace_id: str, document_id: str):
        return SimpleNamespace(job_id="job-lookup", total_chunks=1)

    def get_latest_document_job(self, *, workspace_id: str, document_id: str):
        return SimpleNamespace(job_id="latest-1", workspace_id=workspace_id, document_id=document_id)

    def get_job(self, job_id: str):
        return SimpleNamespace(job_id=job_id, status="running")


@pytest.mark.asyncio
async def test_document_service_starts_extraction_job_on_success(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    class _Jobs:
        async def start_document_job(self, *, workspace_id: str, document_id: str):
            calls.append((workspace_id, document_id))
            return SimpleNamespace(job_id="job-1", total_chunks=1)

    async def fake_ingest_text(self, *, text, filename, metadata, document_id):
        return SimpleNamespace(success=True, total_chunks=3, errors=[])

    svc = DocumentService(extraction_jobs_service=_Jobs())
    svc.repo = _FakeRepo()
    svc.storage = _FakeStorage()

    async def fake_get_vector_store():
        return _FakeVectorStore()

    monkeypatch.setattr(svc, "_get_vector_store", fake_get_vector_store, raising=True)
    monkeypatch.setattr(
        "src.services.document.document_service.IngestService.ingest_text",
        fake_ingest_text,
        raising=True,
    )

    rec = await svc.create_from_upload(
        db=object(),
        filename="a.txt",
        data=b"hello world",
        workspace_id="w1",
    )

    assert rec.status == "completed"
    assert rec.chunks_count == 3
    assert len(calls) == 1
    assert calls[0][0] == "w1"
    assert calls[0][1] == rec.id


@pytest.mark.asyncio
async def test_document_service_keeps_success_if_job_start_fails(monkeypatch) -> None:
    class _Jobs:
        async def start_document_job(self, *, workspace_id: str, document_id: str):
            raise RuntimeError("job start failed")

    async def fake_ingest_text(self, *, text, filename, metadata, document_id):
        return SimpleNamespace(success=True, total_chunks=2, errors=[])

    svc = DocumentService(extraction_jobs_service=_Jobs())
    svc.repo = _FakeRepo()
    svc.storage = _FakeStorage()

    async def fake_get_vector_store():
        return _FakeVectorStore()

    monkeypatch.setattr(svc, "_get_vector_store", fake_get_vector_store, raising=True)
    monkeypatch.setattr(
        "src.services.document.document_service.IngestService.ingest_text",
        fake_ingest_text,
        raising=True,
    )

    rec = await svc.create_from_upload(
        db=object(),
        filename="a.txt",
        data=b"hello world",
        workspace_id="w1",
    )

    assert rec.status == "completed"
    assert rec.chunks_count == 2
    assert rec.error_message is None


def test_document_service_exposes_job_lookup_contract() -> None:
    svc = DocumentService(extraction_jobs_service=_JobsWithLookup())

    latest = svc.get_latest_extraction_job(workspace_id="w1", document_id="d1")
    assert latest is not None
    assert latest.job_id == "latest-1"
    assert latest.workspace_id == "w1"
    assert latest.document_id == "d1"

    by_id = svc.get_extraction_job(job_id="job-42")
    assert by_id is not None
    assert by_id.job_id == "job-42"
    assert by_id.status == "running"
