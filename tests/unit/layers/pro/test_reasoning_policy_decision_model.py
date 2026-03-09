from __future__ import annotations

from src.layers.pro.reasoning.governance.policy_decision_model import (
    build_reasoning_policy_decision,
    build_reasoning_policy_decisions,
)


def test_build_reasoning_policy_decision_normalizes_values():
    row = build_reasoning_policy_decision(
        policy_name="  verify  ",
        status="  warn  ",
        reason="  threshold  ",
    )
    assert row == {
        "policy_name": "verify",
        "status": "warn",
        "reason": "threshold",
    }


def test_build_reasoning_policy_decisions_filters_empty_rows():
    rows = build_reasoning_policy_decisions(
        rows=[
            {"policy_name": " self_check ", "status": " pass ", "reason": " "},
            {"policy_name": "", "status": " ", "reason": ""},
            {"policy_name": "verify", "status": "warn", "reason": "low_coverage"},
        ]
    )
    assert rows == [
        {"policy_name": "self_check", "status": "pass", "reason": ""},
        {"policy_name": "verify", "status": "warn", "reason": "low_coverage"},
    ]


def test_build_reasoning_policy_decisions_handles_empty_input():
    assert build_reasoning_policy_decisions(rows=[]) == []
