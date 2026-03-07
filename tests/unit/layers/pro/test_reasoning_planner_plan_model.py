from __future__ import annotations

from src.layers.pro.reasoning.planner.plan_model import build_reasoning_plan


def test_build_reasoning_plan_keeps_step_order():
    plan = build_reasoning_plan(
        step_descriptions=[
            "find capital of France",
            "confirm country relation",
        ]
    )
    assert plan == {
        "steps": [
            {"description": "find capital of France"},
            {"description": "confirm country relation"},
        ]
    }


def test_build_reasoning_plan_trims_and_skips_empty_steps():
    plan = build_reasoning_plan(
        step_descriptions=[
            "  step one  ",
            "",
            "   ",
            "step two",
        ]
    )
    assert plan == {
        "steps": [
            {"description": "step one"},
            {"description": "step two"},
        ]
    }


def test_build_reasoning_plan_empty_input_returns_empty_plan():
    assert build_reasoning_plan(step_descriptions=[]) == {"steps": []}
