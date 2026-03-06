from __future__ import annotations

import pytest

from src.layers.pro.reasoning.graph.nodes import think_node
from src.layers.pro.reasoning.graph.state import AgentState


class _LLMPlanOnly:
    async def generate(self, prompt: str) -> str:
        return '{"plan": ["search", "reason", "answer"], "reason": "Need evidence first"}'


class _LLMActionConflictsPlan:
    async def generate(self, prompt: str) -> str:
        return '{"action": "ANSWER", "plan": ["search", "reason", "answer"], "reason": "Structured plan should win"}'


class _LLMShouldNotBeCalled:
    def __init__(self):
        self.calls = 0

    async def generate(self, prompt: str) -> str:
        self.calls += 1
        return '{"action":"REASON","reason":"unexpected call"}'


class _LLMInvalidAction:
    async def generate(self, prompt: str) -> str:
        return '{"action":"TOOL","reason":"unsupported action"}'


class _LLMPlainTextAction:
    async def generate(self, prompt: str) -> str:
        return "Next best step is REASON based on available evidence."


@pytest.mark.asyncio
async def test_think_node_uses_structured_plan_when_action_missing():
    state = AgentState(query="Q?", workspace_id="default")
    out = await think_node(state, _LLMPlanOnly())

    assert out.current_action == "SEARCH"
    assert out.plan == ["SEARCH", "REASON", "ANSWER"]
    assert out.iteration_count == 1


@pytest.mark.asyncio
async def test_think_node_prioritizes_plan_over_conflicting_action():
    state = AgentState(query="Q?", workspace_id="default")
    out = await think_node(state, _LLMActionConflictsPlan())

    assert out.current_action == "SEARCH"
    assert out.plan == ["SEARCH", "REASON", "ANSWER"]


@pytest.mark.asyncio
async def test_think_node_advances_structured_plan_steps_between_iterations():
    state = AgentState(query="Q?", workspace_id="default")

    s1 = await think_node(state, _LLMPlanOnly())
    assert s1.current_action == "SEARCH"
    assert s1.current_step == 1

    s2 = await think_node(s1, _LLMPlanOnly())
    assert s2.current_action == "REASON"
    assert s2.current_step == 2

    s3 = await think_node(s2, _LLMPlanOnly())
    assert s3.current_action == "ANSWER"
    assert s3.current_step == 2


@pytest.mark.asyncio
async def test_think_node_forces_answer_when_max_iterations_reached():
    llm = _LLMShouldNotBeCalled()
    state = AgentState(query="Q?", workspace_id="default", iteration_count=10, max_iterations=10)

    out = await think_node(state, llm)

    assert llm.calls == 0
    assert out.current_action == "ANSWER"
    assert out.iteration_count == 11
    assert any("max_iterations" in str(m.get("content", "")) for m in out.messages)


@pytest.mark.asyncio
async def test_think_node_falls_back_to_reason_on_invalid_action():
    state = AgentState(query="Q?", workspace_id="default")
    out = await think_node(state, _LLMInvalidAction())

    assert out.current_action == "REASON"
    assert out.iteration_count == 1


@pytest.mark.asyncio
async def test_think_node_recovers_action_from_plain_text_response():
    state = AgentState(query="Q?", workspace_id="default")
    out = await think_node(state, _LLMPlainTextAction())

    assert out.current_action == "REASON"
    assert out.iteration_count == 1
