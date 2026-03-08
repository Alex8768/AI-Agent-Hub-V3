from __future__ import annotations

import pytest

from src.core.config import settings
from src.core.contracts import VectorDocument
from src.core.exceptions import ValidationError
from src.layers.pro.graph_rag.jobs.runner import EntityExtractionJobRunner
from src.layers.pro.graph_rag.jobs.service import EntityExtractionJobsService


class _FakeVectorStore:
    def __init__(self, docs: dict[str, VectorDocument]) -> None:
        self._document_store = docs


@pytest.mark.asyncio
async def test_start_document_job_success(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    docs = {
        "c1": VectorDocument(
            id="c1",
            content="Alice works at ACME",
            metadata={"workspace_id": "w1", "document_id": "d1"},
        ),
        "c2": VectorDocument(
            id="c2",
            content="ACME is in London",
            metadata={"workspace_id": "w1", "document_id": "d1"},
        ),
        "other": VectorDocument(
            id="other",
            content="ignore me",
            metadata={"workspace_id": "w1", "document_id": "d2"},
        ),
    }

    async def fake_process_chunk(*, workspace_id, document_id, chunk_id, text):
        return {"status": "ok"}

    runner = EntityExtractionJobRunner(process_chunk_fn=fake_process_chunk)
    svc = EntityExtractionJobsService(runner=runner, vector_store=_FakeVectorStore(docs))

    job = await svc.start_document_job(workspace_id="w1", document_id="d1")
    final = await runner.wait(job.job_id, timeout=1.0)
    assert final is not None
    assert final.status == "completed"
    assert final.total_chunks == 2
    assert final.processed_chunks == 2
    latest = svc.get_latest_document_job(workspace_id="w1", document_id="d1")
    assert latest is not None
    assert latest.job_id == job.job_id


@pytest.mark.asyncio
async def test_start_document_job_fails_if_no_chunks(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", True, raising=False)

    docs = {
        "c1": VectorDocument(
            id="c1",
            content="text",
            metadata={"workspace_id": "w1", "document_id": "other-doc"},
        )
    }
    svc = EntityExtractionJobsService(vector_store=_FakeVectorStore(docs))

    with pytest.raises(ValidationError, match="No chunks found for document"):
        await svc.start_document_job(workspace_id="w1", document_id="d1")


@pytest.mark.asyncio
async def test_start_document_job_respects_feature_flag(monkeypatch) -> None:
    monkeypatch.setattr(settings, "feature_graphrag", False, raising=False)
    svc = EntityExtractionJobsService(vector_store=_FakeVectorStore({}))

    with pytest.raises(ValidationError, match="GraphRAG feature is disabled"):
        await svc.start_document_job(workspace_id="w1", document_id="d1")
