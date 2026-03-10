from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import (
    APPROVAL_SESSION_CONTRACT_VERSION,
    ADAPTATION_CONTRACT_VERSION,
    ASSISTANT_CONTRACT_VERSION,
    DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    EXECUTION_PILOT_CONTRACT_VERSION,
    EXECUTION_RECEIPT_CONTRACT_VERSION,
    FEEDBACK_CONTRACT_VERSION,
    HANDSHAKE_CONTRACT_VERSION,
    IDEMPOTENCY_RECORD_CONTRACT_VERSION,
    INTENT_CONTRACT_VERSION,
    LLM_PLANNER_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
    TOOL_SELECTION_CONTRACT_VERSION,
    AssistantApprovalSession,
    AssistantDurableApprovalSessionRecord,
    AssistantDigest,
    AssistantExecutionReceipt,
    AssistantExecutionPilot,
    AssistantFeedbackAdaptation,
    AssistantExecutionHandshake,
    AssistantFeedbackLearning,
    AssistantIdempotencyRecord,
    AssistantIntent,
    AssistantIntentResult,
    AssistantLLMPlanner,
    AssistantPlan,
    AssistantPlanStep,
    AssistantToolSelection,
    AssistantToolSelectionItem,
    AssistantSuggestion,
    DraftAction,
    AnswerRequest,
    AnswerResponse,
    ProvenanceItem,
)


def test_answer_request_defaults():
    req = AnswerRequest(query="What is X?")
    assert req.k == 8
    assert req.graph_depth == 1
    assert req.max_context_chars == 12000
    assert req.filters == {}


def test_answer_request_validation():
    with pytest.raises(Exception):
        AnswerRequest(query="")  # empty query invalid

    with pytest.raises(Exception):
        AnswerRequest(query="q", k=0)

    with pytest.raises(Exception):
        AnswerRequest(query="q", graph_depth=5)


def test_provenance_item_basic():
    p = ProvenanceItem(type="chunk", id="c1")
    assert p.type == "chunk"
    assert p.id == "c1"
    assert p.source_refs == []
    assert p.meta == {}
    assert p.origin == "unknown"
    assert p.reliability is None


def test_answer_response_confidence_bounds():
    with pytest.raises(Exception):
        AnswerResponse(answer="a", confidence=1.5)

    resp = AnswerResponse(answer="a", confidence=0.8)
    assert resp.answer == "a"
    assert resp.confidence == 0.8
    assert resp.provenance == []


def test_provenance_item_origin_and_reliability_validation():
    p = ProvenanceItem(type="memory", id="m1", origin="memory", reliability=0.9)
    assert p.origin == "memory"
    assert p.reliability == 0.9

    with pytest.raises(Exception):
        ProvenanceItem(type="chunk", id="c2", reliability=1.2)


def test_assistant_contract_models_defaults():
    assert ASSISTANT_CONTRACT_VERSION == "v1"
    assert INTENT_CONTRACT_VERSION == "v1"
    assert PLAN_CONTRACT_VERSION == "v1"
    assert LLM_PLANNER_CONTRACT_VERSION == "v1"
    assert TOOL_SELECTION_CONTRACT_VERSION == "v1"
    assert FEEDBACK_CONTRACT_VERSION == "v1"
    assert ADAPTATION_CONTRACT_VERSION == "v1"
    assert HANDSHAKE_CONTRACT_VERSION == "v1"
    assert EXECUTION_RECEIPT_CONTRACT_VERSION == "v1"
    assert APPROVAL_SESSION_CONTRACT_VERSION == "v1"
    assert DURABLE_APPROVAL_SESSION_CONTRACT_VERSION == "v1"
    assert IDEMPOTENCY_RECORD_CONTRACT_VERSION == "v1"
    assert EXECUTION_PILOT_CONTRACT_VERSION == "v1"
    intent = AssistantIntent(intent="start_project", confidence=0.7)
    assert intent.intent == "start_project"
    assert intent.entities == {}
    assert intent.implicit_tasks == []

    draft = DraftAction(action_id="a1", action_type="create_workspace")
    assert draft.status == "draft"
    assert draft.requires_confirmation is True
    assert draft.parameters == {}
    assert draft.preview == {}

    suggestion = AssistantSuggestion(
        suggestion_id="s1",
        title="Prioritize action",
        priority=80,
    )
    digest = AssistantDigest(
        mode="draft_orchestration",
        language="ru",
        summary="Drafts ready",
        suggestions=[suggestion],
        draft_actions=[draft],
        requires_confirmation=True,
    )
    assert digest.mode == "draft_orchestration"
    assert digest.language == "ru"
    assert digest.requires_confirmation is True
    assert len(digest.suggestions) == 1
    assert len(digest.draft_actions) == 1

    intent_result = AssistantIntentResult(intent=intent, reason_codes=["keyword_project"])
    assert intent_result.contract_version == "v1"
    assert intent_result.source == "heuristic"
    assert intent_result.intent.intent == "start_project"
    assert intent_result.reason_codes == ["keyword_project"]

    step = AssistantPlanStep(
        step_id="step:1",
        role="workspace_manager",
        action="prepare_project_workspace_draft",
    )
    plan = AssistantPlan(plan_id="plan:start_project:abc123", status="ready", steps=[step])
    assert plan.contract_version == "v1"
    assert plan.deterministic is True
    assert plan.requires_confirmation is True
    assert len(plan.steps) == 1

    llm_planner = AssistantLLMPlanner(
        source="fallback",
        status="fallback",
        model="gpt-4o-mini",
        intent="start_project",
        plan_id="plan:start_project:abc123",
        reason_codes=["llm_planner_fallback_to_deterministic_plan"],
    )
    assert llm_planner.contract_version == "v1"
    assert llm_planner.status == "fallback"

    tool_selection = AssistantToolSelection(
        status="ready",
        source="deterministic",
        selected_tools=[
            AssistantToolSelectionItem(
                step_id="step:1",
                tool_name="none",
                route="diagnostics_only",
                reason="tool_selection_baseline_no_mapping",
            )
        ],
        reason_codes=["tool_selection_baseline_built"],
    )
    assert tool_selection.contract_version == "v1"
    assert tool_selection.mode == "mcp_aware_selector"
    assert tool_selection.status == "ready"

    feedback = AssistantFeedbackLearning(
        status="ready",
        signals=["approve", "edit"],
        latest_signal="edit",
        signal_counts={"approve": 1, "cancel": 0, "edit": 1},
        reason_codes=["feedback_contract_baseline_built"],
    )
    assert feedback.contract_version == "v1"
    assert feedback.mode == "approve_cancel_edit_feedback"
    assert feedback.status == "ready"

    adaptation = AssistantFeedbackAdaptation(
        status="ready",
        latest_signal="approve",
        boosted_intents=["start_project"],
        suppressed_intents=["general_query"],
        reason_codes=["feedback_adaptation_contract_baseline_built"],
    )
    assert adaptation.contract_version == "v1"
    assert adaptation.mode == "feedback_to_planning_adaptation"
    assert adaptation.status == "ready"

    handshake = AssistantExecutionHandshake(
        state="pending_confirmation",
        requires_confirmation=True,
        confirmation_token="confirm:abc123",
    )
    assert handshake.contract_version == "v1"
    assert handshake.state == "pending_confirmation"
    assert handshake.requires_confirmation is True

    receipt = AssistantExecutionReceipt(
        status="awaiting_confirmation",
        handshake_state="pending_confirmation",
        plan_id="plan:start_project:abc123",
    )
    assert receipt.contract_version == "v1"
    assert receipt.status == "awaiting_confirmation"
    assert receipt.handshake_state == "pending_confirmation"
    assert receipt.rollback_status == "not_applicable"

    approval_session = AssistantApprovalSession(
        approval_id="approval:123",
        workspace_id="default",
        plan_id="plan:start_project:abc123",
        status="open",
        requires_confirmation=True,
        one_time_token="confirm:abc123",
        token_ttl_seconds=900,
    )
    assert approval_session.contract_version == "v1"
    assert approval_session.status == "open"

    durable_record = AssistantDurableApprovalSessionRecord(
        approval_id="approval:123",
        workspace_id="default",
        session_id="default",
        plan_id="plan:start_project:abc123",
        status="open",
        confirmation_token="confirm:abc123",
    )
    assert durable_record.contract_version == "v1"
    assert durable_record.status == "open"

    idempotency_record = AssistantIdempotencyRecord(
        idempotency_key="idem-1",
        workspace_id="default",
        plan_id="plan:start_project:abc123",
        operation_fingerprint="abc123",
        status="fresh",
        decision="approve",
    )
    assert idempotency_record.contract_version == "v1"
    assert idempotency_record.status == "fresh"

    execution_pilot = AssistantExecutionPilot(
        state="ready",
        safe_mode=True,
        execute_enabled=False,
        allowed_action_types=["prepare_summary_draft"],
        requested_action_ids=["draft_action:1"],
        eligible_action_ids=["draft_action:1"],
        blocked_action_ids=[],
    )
    assert execution_pilot.contract_version == "v1"
    assert execution_pilot.mode == "controlled_pilot"
    assert execution_pilot.state == "ready"


def test_assistant_suggestion_priority_validation():
    with pytest.raises(Exception):
        AssistantSuggestion(
            suggestion_id="s2",
            title="Out of range priority",
            priority=101,
        )
