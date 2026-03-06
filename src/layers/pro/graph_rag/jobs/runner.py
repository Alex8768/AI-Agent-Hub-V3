from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from src.layers.pro.graph_rag.extractors.pipeline import process_chunk
from src.layers.pro.graph_rag.jobs.registry import EntityExtractionJob, InMemoryEntityExtractionJobRegistry


@dataclass(frozen=True)
class ExtractionChunkInput:
    chunk_id: str
    text: str


ProcessChunkFn = Callable[..., Awaitable[dict[str, Any]]]


class EntityExtractionJobRunner:
    """Managed async runner for entity extraction jobs."""

    def __init__(
        self,
        *,
        registry: InMemoryEntityExtractionJobRegistry | None = None,
        process_chunk_fn: ProcessChunkFn | None = None,
    ) -> None:
        self._registry = registry or InMemoryEntityExtractionJobRegistry()
        self._process_chunk = process_chunk_fn or process_chunk
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def start_job(
        self,
        *,
        workspace_id: str,
        document_id: str,
        chunks: list[ExtractionChunkInput],
    ) -> EntityExtractionJob:
        job = self._registry.create(
            workspace_id=workspace_id,
            document_id=document_id,
            total_chunks=len(chunks),
        )

        if not chunks:
            self._registry.mark_running(job.job_id)
            self._registry.finalize(job.job_id)
            done = self._registry.get(job.job_id)
            return done if done is not None else job

        task = asyncio.create_task(
            self._run_job(
                job_id=job.job_id,
                workspace_id=workspace_id,
                document_id=document_id,
                chunks=chunks,
            )
        )
        self._tasks[job.job_id] = task

        def _drop_task(_task: asyncio.Task[None], jid: str = job.job_id) -> None:
            self._tasks.pop(jid, None)

        task.add_done_callback(_drop_task)
        return job

    def get_job(self, job_id: str) -> EntityExtractionJob | None:
        return self._registry.get(job_id)

    def is_running(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        return bool(task is not None and not task.done())

    async def wait(self, job_id: str, timeout: float | None = None) -> EntityExtractionJob | None:
        task = self._tasks.get(job_id)
        if task is not None:
            await asyncio.wait_for(task, timeout=timeout)
        return self._registry.get(job_id)

    async def _run_job(
        self,
        *,
        job_id: str,
        workspace_id: str,
        document_id: str,
        chunks: list[ExtractionChunkInput],
    ) -> None:
        self._registry.mark_running(job_id)

        for chunk in chunks:
            try:
                res = await self._process_chunk(
                    workspace_id=workspace_id,
                    document_id=document_id,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                )
                status = str((res or {}).get("status", "error"))
                if status == "ok":
                    self._registry.mark_chunk_result(job_id=job_id, success=True)
                else:
                    reason = str((res or {}).get("reason") or f"chunk_status={status}")
                    self._registry.mark_chunk_result(job_id=job_id, success=False, error=reason)
            except Exception as e:
                self._registry.mark_chunk_result(
                    job_id=job_id,
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                )

        self._registry.finalize(job_id)
