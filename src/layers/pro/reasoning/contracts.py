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
PLAN_CONTRACT_VERSION = "v1"
LLM_PLANNER_CONTRACT_VERSION = "v1"
TOOL_SELECTION_CONTRACT_VERSION = "v1"
FEEDBACK_CONTRACT_VERSION = "v1"
ADAPTATION_CONTRACT_VERSION = "v1"
HANDSHAKE_CONTRACT_VERSION = "v1"
EXECUTION_RECEIPT_CONTRACT_VERSION = "v1"
APPROVAL_SESSION_CONTRACT_VERSION = "v1"
DURABLE_APPROVAL_SESSION_CONTRACT_VERSION = "v1"
IDEMPOTENCY_RECORD_CONTRACT_VERSION = "v1"
EXECUTION_PILOT_CONTRACT_VERSION = "v1"


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


class AssistantPlanStep(BaseModel):
    """Deterministic draft planning step for assistant orchestration."""

    step_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    action: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class AssistantPlan(BaseModel):
    """Deterministic review-only plan produced from extracted intent."""

    contract_version: str = Field(default=PLAN_CONTRACT_VERSION)
    plan_id: str = Field(default="")
    status: Literal["idle", "disabled", "ready"] = Field(default="idle")
    deterministic: bool = Field(default=True)
    intent: str = Field(default="general_query")
    steps: list[AssistantPlanStep] = Field(default_factory=list)
    requires_confirmation: bool = Field(default=True)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantLLMPlanner(BaseModel):
    """LLM planner diagnostics contract (baseline)."""

    contract_version: str = Field(default=LLM_PLANNER_CONTRACT_VERSION)
    source: Literal["heuristic", "llm", "fallback"] = Field(default="heuristic")
    status: Literal["idle", "disabled", "ready", "fallback"] = Field(default="idle")
    model: str = Field(default="")
    intent: str = Field(default="")
    plan_id: str = Field(default="")
    reason_codes: list[str] = Field(default_factory=list)


class AssistantToolSelectionItem(BaseModel):
    """Per-step tool selection record for MCP-aware selector diagnostics."""

    step_id: str = Field(default="")
    tool_name: str = Field(default="")
    route: str = Field(default="")
    reason: str = Field(default="")


class AssistantToolSelection(BaseModel):
    """Tool selection diagnostics contract (baseline)."""

    contract_version: str = Field(default=TOOL_SELECTION_CONTRACT_VERSION)
    mode: Literal["mcp_aware_selector"] = Field(default="mcp_aware_selector")
    status: Literal["idle", "disabled", "ready"] = Field(default="idle")
    source: Literal["none", "deterministic", "mcp"] = Field(default="none")
    selected_tools: list[AssistantToolSelectionItem] = Field(default_factory=list)
    blocked_step_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantFeedbackLearning(BaseModel):
    """Feedback-learning diagnostics contract (baseline)."""

    contract_version: str = Field(default=FEEDBACK_CONTRACT_VERSION)
    mode: Literal["approve_cancel_edit_feedback"] = Field(default="approve_cancel_edit_feedback")
    status: Literal["idle", "disabled", "ready"] = Field(default="idle")
    signals: list[str] = Field(default_factory=list)
    latest_signal: Literal["none", "approve", "cancel", "edit"] = Field(default="none")
    signal_counts: dict[str, int] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantFeedbackAdaptation(BaseModel):
    """Feedback-to-planning adaptation diagnostics contract (baseline)."""

    contract_version: str = Field(default=ADAPTATION_CONTRACT_VERSION)
    mode: Literal["feedback_to_planning_adaptation"] = Field(default="feedback_to_planning_adaptation")
    status: Literal["idle", "disabled", "ready"] = Field(default="idle")
    source: Literal["deterministic"] = Field(default="deterministic")
    latest_signal: Literal["none", "approve", "cancel", "edit"] = Field(default="none")
    boosted_intents: list[str] = Field(default_factory=list)
    suppressed_intents: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantExecutionHandshake(BaseModel):
    """Confirmation-to-execution handshake state (diagnostics contract)."""

    contract_version: str = Field(default=HANDSHAKE_CONTRACT_VERSION)
    state: Literal["idle", "pending_confirmation", "approved", "executed", "cancelled"] = Field(
        default="idle"
    )
    requires_confirmation: bool = Field(default=False)
    confirmation_token: str = Field(default="")
    approved_action_ids: list[str] = Field(default_factory=list)
    blocked_action_ids: list[str] = Field(default_factory=list)
    receipt_id: str = Field(default="")
    reason_codes: list[str] = Field(default_factory=list)


class AssistantExecutionReceipt(BaseModel):
    """Execution receipt stub contract for confirmation lifecycle tracking."""

    contract_version: str = Field(default=EXECUTION_RECEIPT_CONTRACT_VERSION)
    receipt_id: str = Field(default="")
    status: Literal["idle", "awaiting_confirmation", "recorded", "blocked"] = Field(default="idle")
    handshake_state: Literal["idle", "pending_confirmation", "approved", "executed", "cancelled"] = Field(
        default="idle"
    )
    plan_id: str = Field(default="")
    approved_action_ids: list[str] = Field(default_factory=list)
    blocked_action_ids: list[str] = Field(default_factory=list)
    executed_action_ids: list[str] = Field(default_factory=list)
    rollback_status: Literal["not_applicable", "ready", "blocked_missing_rollback_plan"] = Field(
        default="not_applicable"
    )
    rollback_required_action_ids: list[str] = Field(default_factory=list)
    rollback_ready_action_ids: list[str] = Field(default_factory=list)
    rollback_missing_action_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantApprovalSession(BaseModel):
    """Approval session contract for confirmation workflow orchestration."""

    contract_version: str = Field(default=APPROVAL_SESSION_CONTRACT_VERSION)
    approval_id: str = Field(default="")
    workspace_id: str = Field(default="")
    plan_id: str = Field(default="")
    status: Literal["idle", "open", "closed"] = Field(default="idle")
    requires_confirmation: bool = Field(default=False)
    one_time_token: str = Field(default="")
    token_ttl_seconds: int = Field(default=0, ge=0)
    reason_codes: list[str] = Field(default_factory=list)


class AssistantDurableApprovalSessionRecord(BaseModel):
    """Durable approval session record contract (persistence-ready baseline)."""

    contract_version: str = Field(default=DURABLE_APPROVAL_SESSION_CONTRACT_VERSION)
    approval_id: str = Field(default="")
    workspace_id: str = Field(default="")
    session_id: str = Field(default="default")
    plan_id: str = Field(default="")
    status: Literal["idle", "open", "closed"] = Field(default="idle")
    confirmation_token: str = Field(default="")
    token_expires_at: str = Field(default="")
    last_decision: Literal["", "approve", "cancel"] = Field(default="")
    reason_codes: list[str] = Field(default_factory=list)


class AssistantIdempotencyRecord(BaseModel):
    """Durable idempotency record contract (persistence-ready baseline)."""

    contract_version: str = Field(default=IDEMPOTENCY_RECORD_CONTRACT_VERSION)
    idempotency_key: str = Field(default="")
    workspace_id: str = Field(default="")
    plan_id: str = Field(default="")
    operation_fingerprint: str = Field(default="")
    status: Literal["none", "fresh", "replayed", "conflict"] = Field(default="none")
    confirmation_token: str = Field(default="")
    decision: Literal["", "approve", "cancel"] = Field(default="")
    reason_codes: list[str] = Field(default_factory=list)


class AssistantExecutionPilot(BaseModel):
    """Controlled execution pilot diagnostics contract (baseline)."""

    contract_version: str = Field(default=EXECUTION_PILOT_CONTRACT_VERSION)
    mode: Literal["controlled_pilot"] = Field(default="controlled_pilot")
    state: Literal["idle", "disabled", "awaiting_confirmation", "ready", "blocked", "executed"] = Field(
        default="idle"
    )
    safe_mode: bool = Field(default=True)
    execute_enabled: bool = Field(default=False)
    max_actions_per_run: int = Field(default=1, ge=0)
    allowed_action_types: list[str] = Field(default_factory=list)
    requested_action_ids: list[str] = Field(default_factory=list)
    eligible_action_ids: list[str] = Field(default_factory=list)
    blocked_action_ids: list[str] = Field(default_factory=list)
    executed_action_ids: list[str] = Field(default_factory=list)
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
