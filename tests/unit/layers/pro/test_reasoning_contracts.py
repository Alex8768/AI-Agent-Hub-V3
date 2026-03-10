from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import (
    ASSISTANT_CONTRACT_VERSION,
    INTENT_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
    AssistantDigest,
    AssistantIntent,
    AssistantIntentResult,
    AssistantPlan,
    AssistantPlanStep,
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


def test_assistant_suggestion_priority_validation():
    with pytest.raises(Exception):
        AssistantSuggestion(
            suggestion_id="s2",
            title="Out of range priority",
            priority=101,
        )
