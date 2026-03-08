from __future__ import annotations

from src.layers.pro.graph_rag.jobs.registry import InMemoryEntityExtractionJobRegistry


def test_registry_job_lifecycle_success() -> None:
    reg = InMemoryEntityExtractionJobRegistry()
    job = reg.create(workspace_id="w1", document_id="d1", total_chunks=2)

    assert job.status == "queued"
    assert job.processed_chunks == 0
    assert job.success_chunks == 0
    assert job.failed_chunks == 0

    running = reg.mark_running(job.job_id)
    assert running is not None
    assert running.status == "running"
    assert running.started_at is not None

    step1 = reg.mark_chunk_result(job_id=job.job_id, success=True)
    assert step1 is not None
    assert step1.processed_chunks == 1
    assert step1.success_chunks == 1
    assert step1.failed_chunks == 0

    step2 = reg.mark_chunk_result(job_id=job.job_id, success=True)
    assert step2 is not None
    assert step2.processed_chunks == 2
    assert step2.success_chunks == 2
    assert step2.failed_chunks == 0

    done = reg.finalize(job.job_id)
    assert done is not None
    assert done.status == "completed"
    assert done.finished_at is not None
    assert done.errors == ()


def test_registry_job_lifecycle_failure() -> None:
    reg = InMemoryEntityExtractionJobRegistry()
    job = reg.create(workspace_id="w1", document_id="d2", total_chunks=2)
    reg.mark_running(job.job_id)

    reg.mark_chunk_result(job_id=job.job_id, success=True)
    reg.mark_chunk_result(job_id=job.job_id, success=False, error="chunk c2 failed")

    done = reg.finalize(job.job_id)
    assert done is not None
    assert done.status == "failed"
    assert done.processed_chunks == 2
    assert done.success_chunks == 1
    assert done.failed_chunks == 1
    assert done.errors == ("chunk c2 failed",)


def test_registry_returns_none_for_unknown_job() -> None:
    reg = InMemoryEntityExtractionJobRegistry()

    assert reg.get("missing") is None
    assert reg.mark_running("missing") is None
    assert reg.mark_chunk_result(job_id="missing", success=True) is None
    assert reg.finalize("missing") is None
    assert reg.get_latest_by_document(workspace_id="w1", document_id="d1") is None


def test_registry_tracks_latest_job_per_document() -> None:
    reg = InMemoryEntityExtractionJobRegistry()

    first = reg.create(workspace_id="w1", document_id="d1", total_chunks=1)
    second = reg.create(workspace_id="w1", document_id="d1", total_chunks=2)

    latest = reg.get_latest_by_document(workspace_id="w1", document_id="d1")
    assert latest is not None
    assert latest.job_id == second.job_id
    assert latest.job_id != first.job_id
