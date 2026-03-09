from __future__ import annotations

from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)
from src.layers.pro.reasoning.enterprise.rollout_decision_model import (
    build_enterprise_rollout_decision,
    decide_enterprise_rollout_action,
)


def test_build_enterprise_rollout_decision_normalizes_values():
    decision = build_enterprise_rollout_decision(
        decision_id=" d-1 ",
        action=" APPROVE ",
        target_environment=" prod ",
        blocked_by=["verify", " verify ", ""],
        reason_codes=["ok", " ok "],
        confidence="1.5",
        requires_human_approval=0,
    )
    assert decision == {
        "decision_id": "d-1",
        "action": "approve",
        "target_environment": "prod",
        "blocked_by": ["verify"],
        "reason_codes": ["ok"],
        "confidence": 1.0,
        "requires_human_approval": False,
    }


def test_decide_enterprise_rollout_action_approves_when_ready():
    readiness = build_enterprise_readiness_contract(
        profile_name="prod",
        release_gate_passed=True,
        failed_checks=[],
        benchmark_pass_rate=0.95,
        benchmark_average_score=0.9,
        optimization_action="approve",
        optimization_requires_review=False,
        warnings_count=0,
        reason_codes=[],
    )
    policy = build_enterprise_release_gate_policy(
        profile_name="prod",
        allow_skipped=False,
        require_optimization_review=True,
    )
    decision = decide_enterprise_rollout_action(readiness=readiness, policy=policy)
    assert decision["action"] == "approve"
    assert decision["requires_human_approval"] is False
    assert "enterprise_gate_satisfied" in decision["reason_codes"]


def test_decide_enterprise_rollout_action_rejects_when_release_gate_fails():
    readiness = build_enterprise_readiness_contract(
        profile_name="prod",
        release_gate_passed=False,
        failed_checks=["verify"],
        benchmark_pass_rate=0.2,
        benchmark_average_score=0.3,
        optimization_action="approve",
        optimization_requires_review=False,
        warnings_count=0,
        reason_codes=["blocking_checks_failed"],
    )
    policy = build_enterprise_release_gate_policy(profile_name="prod")
    decision = decide_enterprise_rollout_action(readiness=readiness, policy=policy)
    assert decision["action"] == "reject"
    assert decision["blocked_by"] == ["verify"]
    assert "release_gate_not_passed" in decision["reason_codes"]
    assert decision["requires_human_approval"] is True


def test_decide_enterprise_rollout_action_defers_on_review_or_warnings():
    readiness = build_enterprise_readiness_contract(
        profile_name="prod",
        release_gate_passed=True,
        failed_checks=[],
        benchmark_pass_rate=0.9,
        benchmark_average_score=0.9,
        optimization_action="defer",
        optimization_requires_review=True,
        warnings_count=1,
        reason_codes=[],
    )
    policy = build_enterprise_release_gate_policy(
        profile_name="prod",
        allow_skipped=False,
        require_optimization_review=True,
    )
    decision = decide_enterprise_rollout_action(readiness=readiness, policy=policy)
    assert decision["action"] == "defer"
    assert "manual_optimization_review_required" in decision["reason_codes"]
    assert decision["requires_human_approval"] is True
