from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchServiceRequest(BaseModel):
    query: str
    k: int = Field(5, ge=1, le=50)
    filters: dict[str, Any] | None = None
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    include_content: bool = False
    snippet_len: int = Field(240, ge=50, le=2000)
    include_metadata: bool = True
    evidence_max_total: int = Field(50, ge=1, le=500)
    evidence_max_chunks: int | None = Field(default=None, ge=0, le=200)
    evidence_max_memory: int | None = Field(default=None, ge=0, le=200)
    evidence_max_edges: int | None = Field(default=None, ge=0, le=200)
    evidence_dedupe: bool = True
    evidence_rerank: bool = True


class SearchServiceResult(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    snippet: str
    content: str | None = None
    source_document: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
