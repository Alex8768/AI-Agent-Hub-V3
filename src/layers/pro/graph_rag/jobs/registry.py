from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import RLock
from typing import Literal
from uuid import uuid4


JobStatus = Literal["queued", "running", "completed", "failed"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EntityExtractionJob:
    job_id: str
    workspace_id: str
    document_id: str
    total_chunks: int
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    processed_chunks: int = 0
    success_chunks: int = 0
    failed_chunks: int = 0
    errors: tuple[str, ...] = ()


class InMemoryEntityExtractionJobRegistry:
    """Thread-safe in-memory registry for extraction job status."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._jobs: dict[str, EntityExtractionJob] = {}

    def create(self, *, workspace_id: str, document_id: str, total_chunks: int) -> EntityExtractionJob:
        job = EntityExtractionJob(
            job_id=uuid4().hex,
            workspace_id=workspace_id,
            document_id=document_id,
            total_chunks=max(0, int(total_chunks)),
            status="queued",
            created_at=_utcnow(),
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> EntityExtractionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> EntityExtractionJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            started_at = job.started_at or _utcnow()
            updated = replace(job, status="running", started_at=started_at)
            self._jobs[job_id] = updated
            return updated

    def mark_chunk_result(self, *, job_id: str, success: bool, error: str | None = None) -> EntityExtractionJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            processed = job.processed_chunks + 1
            success_chunks = job.success_chunks + (1 if success else 0)
            failed_chunks = job.failed_chunks + (0 if success else 1)

            errors = job.errors
            if error:
                errors = (*errors, error)

            updated = replace(
                job,
                processed_chunks=processed,
                success_chunks=success_chunks,
                failed_chunks=failed_chunks,
                errors=errors,
            )
            self._jobs[job_id] = updated
            return updated

    def finalize(self, job_id: str) -> EntityExtractionJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            status: JobStatus = "failed" if job.failed_chunks > 0 else "completed"
            updated = replace(job, status=status, finished_at=_utcnow())
            self._jobs[job_id] = updated
            return updated
