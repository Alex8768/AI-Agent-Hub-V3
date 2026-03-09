from __future__ import annotations

from src.layers.pro.reasoning.engine import ReasoningEngine
from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)
from src.layers.pro.reasoning.enterprise.rollout_decision_model import (
    decide_enterprise_rollout_action,
)


def _diagnostics_payload() -> dict[str, object]:
    return {
        "trace_id": "trace-enterprise-1",
        "verify": {"status": "pass"},
        "self_check": {"status": "pass"},
        "reasoning_benchmark": {
            "summary": {"pass_rate": 0.85, "average_score": 0.82},
            "average_latency_ms": 50,
        },
        "reasoning_optimization": {
            "decision": {
                "action": "approve",
                "requires_human_review": False,
            }
        },
    }


def test_enterprise_quality_gate_contract_builders_are_deterministic():
    diagnostics = _diagnostics_payload()
    policy_a = build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )
    policy_b = build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )
    assert policy_a == policy_b

    readiness_a = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            **diagnostics,
            "release_checks": {
                "verify": "pass",
                "self_check": "pass",
                "reasoning_benchmark": "pass",
                "reasoning_optimization": "pass",
            },
        },
        policy=policy_a,
        warnings=[],
    )
    readiness_b = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            **diagnostics,
            "release_checks": {
                "verify": "pass",
                "self_check": "pass",
                "reasoning_benchmark": "pass",
                "reasoning_optimization": "pass",
            },
        },
        policy=policy_b,
        warnings=[],
    )
    assert readiness_a == readiness_b


def test_enterprise_quality_gate_rollout_boundaries_are_stable():
    policy = build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        allow_skipped=False,
        require_optimization_review=True,
    )
    diagnostics = _diagnostics_payload()
    readiness = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            **diagnostics,
            "release_checks": {"verify": "pass", "self_check": "pass"},
        },
        policy=policy,
        warnings=[],
    )
    decision = decide_enterprise_rollout_action(
        readiness=readiness,
        policy=policy,
        decision_id="enterprise_rollout:test",
        target_environment="production",
    )
    assert decision["action"] == "approve"
    assert decision["requires_human_approval"] is False
    assert "enterprise_gate_satisfied" in decision["reason_codes"]

    failing_readiness = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            **diagnostics,
            "release_checks": {"verify": "warn", "self_check": "pass"},
            "reasoning_optimization": {"decision": {"action": "reject", "requires_human_review": True}},
        },
        policy=policy,
        warnings=["verify_warning"],
    )
    failing_decision = decide_enterprise_rollout_action(
        readiness=failing_readiness,
        policy=policy,
        decision_id="enterprise_rollout:test",
        target_environment="production",
    )
    assert failing_decision["action"] == "reject"
    assert failing_decision["requires_human_approval"] is True
    assert "release_gate_not_passed" in failing_decision["reason_codes"]


def test_enterprise_quality_gate_runtime_contract_shape():
    runtime = ReasoningEngine._build_enterprise_productization_diagnostics(
        diagnostics=_diagnostics_payload(),
        warnings=[],
    )
    assert set(runtime.keys()) == {
        "release_gate_policy",
        "release_checks",
        "readiness",
        "rollout_decision",
    }
    policy = dict(runtime["release_gate_policy"])
    assert set(policy.keys()) == {
        "profile_name",
        "required_checks",
        "blocking_checks",
        "minimum_pass_rate",
        "minimum_average_score",
        "minimum_coverage_ratio",
        "allow_skipped",
        "require_benchmark_summary",
        "require_optimization_review",
        "allowed_warning_codes",
    }
    assert isinstance(runtime["release_checks"], dict)
    readiness = dict(runtime["readiness"])
    assert set(readiness.keys()) == {
        "profile_name",
        "release_gate_passed",
        "failed_checks",
        "benchmark_pass_rate",
        "benchmark_average_score",
        "optimization_action",
        "optimization_requires_review",
        "warnings_count",
        "readiness_score",
        "reason_codes",
    }
    decision = dict(runtime["rollout_decision"])
    assert set(decision.keys()) == {
        "decision_id",
        "action",
        "target_environment",
        "blocked_by",
        "reason_codes",
        "confidence",
        "requires_human_approval",
    }


def test_enterprise_quality_gate_runtime_matches_direct_contracts():
    diagnostics = _diagnostics_payload()
    warnings = ["verify_warning"]
    runtime = ReasoningEngine._build_enterprise_productization_diagnostics(
        diagnostics=diagnostics,
        warnings=warnings,
    )
    direct_policy = dict(runtime["release_gate_policy"])
    direct_readiness = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            **diagnostics,
            "release_checks": dict(runtime["release_checks"]),
        },
        policy=direct_policy,
        warnings=warnings,
    )
    direct_rollout = decide_enterprise_rollout_action(
        readiness=direct_readiness,
        policy=direct_policy,
        decision_id=dict(runtime["rollout_decision"]).get("decision_id", "enterprise_rollout:runtime"),
        target_environment=dict(runtime["rollout_decision"]).get("target_environment", "production"),
    )
    assert dict(runtime["readiness"]) == direct_readiness
    assert dict(runtime["rollout_decision"]) == direct_rollout
