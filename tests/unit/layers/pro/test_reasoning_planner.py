from __future__ import annotations

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
