from __future__ import annotations

from src.layers.pro.reasoning.multi_agent.coordination_model import (
    build_multi_agent_coordination_plan,
)
from src.layers.pro.reasoning.multi_agent.handoff_router import (
    route_multi_agent_handoffs,
)


def test_route_multi_agent_handoffs_builds_expected_transitions():
    plan = build_multi_agent_coordination_plan(
        query="q",
        steps=[
            {
                "step_index": 0,
                "agent_role": "researcher",
                "objective": "collect",
                "input_keys": ["query"],
                "output_key": "evidence",
                "depends_on": [],
            },
            {
                "step_index": 1,
                "agent_role": "critic",
                "objective": "check",
                "input_keys": ["evidence"],
                "output_key": "critique",
                "depends_on": [0],
            },
            {
                "step_index": 2,
                "agent_role": "synthesizer",
                "objective": "answer",
                "input_keys": ["evidence", "critique"],
                "output_key": "answer_draft",
                "depends_on": [0, 1],
            },
        ],
    )
    transitions = route_multi_agent_handoffs(plan=plan)
    assert transitions == [
        {
            "from_step_index": 0,
            "to_step_index": 1,
            "from_role": "researcher",
            "to_role": "critic",
            "output_key": "evidence",
            "accepted": True,
            "reason": "handoff_output_key_consumed",
        },
        {
            "from_step_index": 0,
            "to_step_index": 2,
            "from_role": "researcher",
            "to_role": "synthesizer",
            "output_key": "evidence",
            "accepted": True,
            "reason": "handoff_output_key_consumed",
        },
        {
            "from_step_index": 1,
            "to_step_index": 2,
            "from_role": "critic",
            "to_role": "synthesizer",
            "output_key": "critique",
            "accepted": True,
            "reason": "handoff_output_key_consumed",
        },
    ]


def test_route_multi_agent_handoffs_marks_unconsumed_outputs():
    plan = build_multi_agent_coordination_plan(
        query="q",
        steps=[
            {
                "step_index": 0,
                "agent_role": "researcher",
                "objective": "collect",
                "input_keys": ["query"],
                "output_key": "evidence",
                "depends_on": [],
            },
            {
                "step_index": 1,
                "agent_role": "critic",
                "objective": "check",
                "input_keys": ["query_only"],
                "output_key": "critique",
                "depends_on": [0],
            },
        ],
    )
    transitions = route_multi_agent_handoffs(plan=plan)
    assert transitions == [
        {
            "from_step_index": 0,
            "to_step_index": 1,
            "from_role": "researcher",
            "to_role": "critic",
            "output_key": "evidence",
            "accepted": False,
            "reason": "handoff_output_key_not_consumed",
        }
    ]


def test_route_multi_agent_handoffs_handles_empty_plan():
    plan = build_multi_agent_coordination_plan(query="", steps=[])
    assert route_multi_agent_handoffs(plan=plan) == []
