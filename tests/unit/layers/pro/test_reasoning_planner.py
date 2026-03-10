from __future__ import annotations

from src.layers.pro.composition.registry import AgentRegistry
from src.layers.pro.reasoning.contracts import AnswerRequest
from src.layers.pro.reasoning.planner.planner import create_reasoning_plan


def test_create_reasoning_plan_returns_empty_for_blank_query():
    assert create_reasoning_plan(query="") == {"steps": []}
    assert create_reasoning_plan(query="   ") == {"steps": []}


def test_create_reasoning_plan_single_step_for_simple_query():
    plan = create_reasoning_plan(query="What is RAG?")
    assert plan == {
        "steps": [
            {"description": "Answer query using verified evidence: What is RAG"},
        ]
    }


def test_create_reasoning_plan_two_steps_when_split_hints_present():
    plan = create_reasoning_plan(query="Find capital of France and confirm country relation")
    assert plan == {
        "steps": [
            {"description": "Analyze query intent: Find capital of France and confirm country relation"},
            {
                "description": (
                    "Synthesize final answer from verified evidence: "
                    "Find capital of France and confirm country relation"
                )
            },
        ]
    }


def test_create_reasoning_plan_accepts_answer_request_query_input():
    plan = create_reasoning_plan(query=AnswerRequest(query="  What is RAG? "))
    assert plan == {
        "steps": [
            {"description": "Answer query using verified evidence: What is RAG"},
        ]
    }


def test_create_reasoning_plan_returns_composition_graph_when_enabled() -> None:
    registry = AgentRegistry()
    registry.register(
        {
            "agent_id": "planner-agent",
            "display_name": "Planner Agent",
            "capabilities": ["plan"],
            "output_schema": {"properties": {"plan": {"type": "string"}}},
            "enabled": True,
        }
    )
    registry.register(
        {
            "agent_id": "executor-agent",
            "display_name": "Executor Agent",
            "capabilities": ["execute"],
            "input_schema": {"properties": {"plan": {"type": "string"}}},
            "enabled": True,
        }
    )
    plan = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=registry,
    )
    assert plan["composition_mode"] is True
    assert plan["reason_codes"] == []
    graph = plan.get("composition_graph") or {}
    assert graph.get("entry_node_id") == "plan"
    assert graph.get("exit_node_id") == "exec"
    assert len(list(graph.get("nodes") or [])) == 2


def test_create_reasoning_plan_composition_mode_falls_back_safely() -> None:
    plan = create_reasoning_plan(
        query="Summarize launch risks",
        composition_mode=True,
        composition_registry=AgentRegistry(),
    )
    assert plan["composition_mode"] is True
    assert plan["reason_codes"] == ["composition_graph_unavailable"]
    assert "composition_graph" not in plan
    assert plan["steps"] == [{"description": "Answer query using verified evidence: Summarize launch risks"}]
