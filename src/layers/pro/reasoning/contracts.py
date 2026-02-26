from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ProvenanceType = Literal["chunk", "node", "edge"]


class ProvenanceItem(BaseModel):
    """A single piece of evidence provenance used for answer synthesis."""

    type: ProvenanceType
    id: str = Field(min_length=1)

    # For UI / audit: references to source documents/chunks/etc.
    source_refs: list[str] = Field(default_factory=list)

    # Optional scoring metadata (not all retrievers provide this).
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    # Optional extra metadata (kept generic to avoid coupling).
    meta: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Normalized evidence collected from retrieval and graph expansion."""

    chunks: list[str] = Field(default_factory=list)
    nodes: list[str] = Field(default_factory=list)
    edges: list[str] = Field(default_factory=list)

    provenance: list[ProvenanceItem] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    """Domain-level request for graph-aware answer synthesis."""

    query: str = Field(min_length=1)
    k: int = Field(default=8, ge=1, le=50)

    # Graph expansion policy (MVP).
    graph_depth: int = Field(default=1, ge=0, le=3)

    # Context packing budget (MVP: chars; token budgeting can come later).
    max_context_chars: int = Field(default=12000, ge=1000, le=200000)

    # Optional filters (workspace, doc_ids, tags, etc.), kept generic.
    filters: dict[str, Any] = Field(default_factory=dict)


class AnswerResponse(BaseModel):
    """Domain-level response: answer + provenance + confidence."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)

    # Deterministic packed preview of context evidence (MVP, UI-friendly)
    context_preview: str = Field(default="")

    provenance: list[ProvenanceItem] = Field(default_factory=list)

    # For diagnostics / UI (ids only; full graph is returned by retrieval endpoints).
    used_chunks: list[str] = Field(default_factory=list)
    used_nodes: list[str] = Field(default_factory=list)
    used_edges: list[str] = Field(default_factory=list)

    # API-level correlation (set by the API layer; safe defaults keep compatibility)
    request_id: str = Field(default="")
    workspace_id: str = Field(default="")

    # Minimal performance envelope (ms). Extended timings can be added later.
    timings: dict[str, float] = Field(default_factory=dict)

    # Warnings for clients/UI (e.g., llm_missing, fallback_used, timeout)
    warnings: list[str] = Field(default_factory=list)

    # Diagnostics for clients/UI (explainability counters, flags, small metadata)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
