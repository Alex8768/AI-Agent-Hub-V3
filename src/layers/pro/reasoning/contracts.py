from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ProvenanceType = Literal["chunk", "node", "edge", "memory"]
ProvenanceOrigin = Literal["vector", "graph", "memory", "planner", "unknown"]
EVIDENCE_CONTRACT_VERSION = "v1"
VERIFY_DIAGNOSTICS_VERSION = "v1"
VERIFY_SELF_CHECK_STATUS_REQUIRED = "pass"
VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED = "warning_only"
VERIFY_SELF_CHECK_REASONS_COUNT_MAX = 0
SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN = 1.0
SELF_CHECK_MISSING_MINIMAL_COUNT_MAX = 0
ASSISTANT_CONTRACT_VERSION = "v1"
INTENT_CONTRACT_VERSION = "v1"


class ProvenanceItem(BaseModel):
    """A single piece of evidence provenance used for answer synthesis."""

    type: ProvenanceType
    id: str = Field(min_length=1)

    # For UI / audit: references to source documents/chunks/etc.
    source_refs: list[str] = Field(default_factory=list)

    # Optional scoring metadata (not all retrievers provide this).
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    origin: ProvenanceOrigin = Field(default="unknown")
    reliability: float | None = Field(default=None, ge=0.0, le=1.0)

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
    # Session-scoped correlation for incremental memory (A2.1).
    session_id: str = Field(default="default", min_length=1, max_length=128)
    # Best-effort loaded session context (set by orchestration layer).
    session_memory_last_answer: str = Field(default="", max_length=4000)

    # Hybrid evidence policy controls (A1.5)
    evidence_max_total: int = Field(default=50, ge=1, le=500)
    evidence_max_chunks: int | None = Field(default=None, ge=0, le=200)
    evidence_max_memory: int | None = Field(default=None, ge=0, le=200)
    evidence_max_edges: int | None = Field(default=None, ge=0, le=200)
    evidence_dedupe: bool = Field(default=True)
    evidence_rerank: bool = Field(default=True)


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


AssistantResponseMode = Literal["strict_rag", "assistant_fallback", "draft_orchestration"]
AssistantActionStatus = Literal["draft", "requires_confirmation", "approved", "executed", "cancelled"]


class AssistantIntent(BaseModel):
    """Normalized intent extracted from free-form user request."""

    intent: str = Field(min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    implicit_tasks: list[str] = Field(default_factory=list)


class AssistantIntentResult(BaseModel):
    """Intent extraction result contract used by assistant orchestration."""

    contract_version: str = Field(default=INTENT_CONTRACT_VERSION)
    source: Literal["heuristic", "llm", "manual"] = Field(default="heuristic")
    intent: AssistantIntent
    reason_codes: list[str] = Field(default_factory=list)


class DraftAction(BaseModel):
    """Safe draft action contract for assistant runtime planning."""

    action_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: AssistantActionStatus = Field(default="draft")
    requires_confirmation: bool = Field(default=True)
    estimated_impact: str = Field(default="")
    preview: dict[str, Any] = Field(default_factory=dict)
    rollback_plan: str = Field(default="")


class AssistantSuggestion(BaseModel):
    """User-facing proactive suggestion item."""

    suggestion_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rationale: str = Field(default="")
    priority: int = Field(default=50, ge=0, le=100)
    action_hint: str = Field(default="")


class AssistantDigest(BaseModel):
    """Assistant digest bundle for review-before-execute workflows."""

    mode: AssistantResponseMode = Field(default="strict_rag")
    language: str = Field(default="auto")
    summary: str = Field(default="")
    suggestions: list[AssistantSuggestion] = Field(default_factory=list)
    draft_actions: list[DraftAction] = Field(default_factory=list)
    requires_confirmation: bool = Field(default=False)
