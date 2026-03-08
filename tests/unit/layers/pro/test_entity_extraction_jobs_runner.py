from __future__ import annotations

import pytest

from src.layers.pro.graph_rag.jobs.runner import EntityExtractionJobRunner, ExtractionChunkInput


@pytest.mark.asyncio
async def test_runner_completes_job_successfully() -> None:
    async def fake_process_chunk(*, workspace_id, document_id, chunk_id, text):
        return {"status": "ok", "entities": 1, "relations": 0}

    runner = EntityExtractionJobRunner(process_chunk_fn=fake_process_chunk)
    job = runner.start_job(
        workspace_id="w1",
        document_id="d1",
        chunks=[
            ExtractionChunkInput(chunk_id="c1", text="a"),
            ExtractionChunkInput(chunk_id="c2", text="b"),
        ],
    )

    final = await runner.wait(job.job_id, timeout=1.0)
    assert final is not None
    assert final.status == "completed"
    assert final.total_chunks == 2
    assert final.processed_chunks == 2
    assert final.success_chunks == 2
    assert final.failed_chunks == 0
    assert final.errors == ()
    assert runner.is_running(job.job_id) is False


@pytest.mark.asyncio
async def test_runner_marks_job_failed_when_chunk_fails() -> None:
    async def fake_process_chunk(*, workspace_id, document_id, chunk_id, text):
        if chunk_id == "c2":
            raise RuntimeError("boom")
        return {"status": "ok"}

    runner = EntityExtractionJobRunner(process_chunk_fn=fake_process_chunk)
    job = runner.start_job(
        workspace_id="w1",
        document_id="d2",
        chunks=[
            ExtractionChunkInput(chunk_id="c1", text="a"),
            ExtractionChunkInput(chunk_id="c2", text="b"),
        ],
    )

    final = await runner.wait(job.job_id, timeout=1.0)
    assert final is not None
    assert final.status == "failed"
    assert final.processed_chunks == 2
    assert final.success_chunks == 1
    assert final.failed_chunks == 1
    assert len(final.errors) == 1
    assert "RuntimeError: boom" in final.errors[0]
    assert runner.is_running(job.job_id) is False


@pytest.mark.asyncio
async def test_runner_empty_chunks_finishes_immediately() -> None:
    runner = EntityExtractionJobRunner()
    job = runner.start_job(workspace_id="w1", document_id="d3", chunks=[])

    final = await runner.wait(job.job_id, timeout=1.0)
    assert final is not None
    assert final.status == "completed"
    assert final.total_chunks == 0
    assert final.processed_chunks == 0
