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
