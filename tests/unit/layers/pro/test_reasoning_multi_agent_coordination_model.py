from __future__ import annotations

from src.layers.pro.reasoning.multi_agent.coordination_model import (
    build_multi_agent_arbitration_decision,
    build_multi_agent_coordination_plan,
    build_multi_agent_coordination_step,
)


def test_build_multi_agent_coordination_step_normalizes_fields():
    row = build_multi_agent_coordination_step(
        step_index="2",
        agent_role="  researcher  ",
        objective="  gather evidence  ",
        input_keys=[" query ", "", "workspace_id"],
        output_key="  evidence_set  ",
        depends_on=[0, "1", -1, "x", 1],
    )
    assert row == {
        "step_index": 2,
        "agent_role": "researcher",
        "objective": "gather evidence",
        "input_keys": ["query", "workspace_id"],
        "output_key": "evidence_set",
        "depends_on": [0, 1],
    }


def test_build_multi_agent_coordination_plan_builds_stable_shape():
    plan = build_multi_agent_coordination_plan(
        query="  answer question  ",
        steps=[
            {
                "agent_role": "researcher",
                "objective": "find evidence",
                "input_keys": ["query"],
                "output_key": "evidence",
                "depends_on": [],
            },
            {
                "step_index": 5,
                "agent_role": "synthesizer",
                "objective": "compose final answer",
                "input_keys": ["evidence"],
                "output_key": "answer_draft",
                "depends_on": [0],
            },
        ],
    )
    assert plan == {
        "query": "answer question",
        "steps": [
            {
                "step_index": 0,
                "agent_role": "researcher",
                "objective": "find evidence",
                "input_keys": ["query"],
                "output_key": "evidence",
                "depends_on": [],
            },
            {
                "step_index": 5,
                "agent_role": "synthesizer",
                "objective": "compose final answer",
                "input_keys": ["evidence"],
                "output_key": "answer_draft",
                "depends_on": [0],
            },
        ],
    }


def test_build_multi_agent_arbitration_decision_normalizes_values():
    decision = build_multi_agent_arbitration_decision(
        winner_role="  critic  ",
        strategy="  consensus  ",
        reasons=[" low_risk ", "", "high_coverage"],
        confidence_score=1.9,
    )
    assert decision == {
        "winner_role": "critic",
        "strategy": "consensus",
        "reasons": ["low_risk", "high_coverage"],
        "confidence_score": 1.0,
    }
