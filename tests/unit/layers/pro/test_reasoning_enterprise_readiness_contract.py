from __future__ import annotations

from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract,
    build_enterprise_readiness_contract_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)


def test_build_enterprise_readiness_contract_normalizes_values():
    contract = build_enterprise_readiness_contract(
        profile_name=" prod ",
        release_gate_passed=1,
        failed_checks=[" ci/lint ", "ci/lint", ""],
        benchmark_pass_rate="1.4",
        benchmark_average_score="-1",
        optimization_action=" APPROVE ",
        optimization_requires_review=0,
        warnings_count="-3",
        reason_codes=["ok", " ok "],
    )
    assert contract == {
        "profile_name": "prod",
        "release_gate_passed": True,
        "failed_checks": ["ci/lint"],
        "benchmark_pass_rate": 1.0,
        "benchmark_average_score": 0.0,
        "optimization_action": "approve",
        "optimization_requires_review": False,
        "warnings_count": 0,
        "readiness_score": 0.5,
        "reason_codes": ["ok"],
    }


def test_build_enterprise_readiness_contract_from_diagnostics_pass_path():
    policy = build_enterprise_release_gate_policy(
        profile_name="prod",
        required_checks=["verify", "self_check"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
    )
    contract = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            "release_checks": {"verify": "pass", "self_check": "pass"},
            "reasoning_benchmark": {"summary": {"pass_rate": 0.9, "average_score": 0.8}},
            "reasoning_optimization": {"decision": {"action": "approve", "requires_human_review": False}},
        },
        policy=policy,
        warnings=[],
    )
    assert contract["profile_name"] == "prod"
    assert contract["release_gate_passed"] is True
    assert contract["failed_checks"] == []
    assert contract["benchmark_pass_rate"] == 0.9
    assert contract["benchmark_average_score"] == 0.8
    assert contract["optimization_action"] == "approve"
    assert contract["optimization_requires_review"] is False
    assert contract["reason_codes"] == []


def test_build_enterprise_readiness_contract_from_diagnostics_collects_fail_reasons():
    policy = build_enterprise_release_gate_policy(
        profile_name="prod",
        blocking_checks=["verify"],
        minimum_pass_rate=0.95,
        minimum_average_score=0.9,
    )
    contract = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={
            "release_checks": {"verify": "warn"},
            "reasoning_benchmark": {"summary": {"pass_rate": 0.2, "average_score": 0.3}},
            "reasoning_optimization": {"decision": {"action": "reject", "requires_human_review": True}},
        },
        policy=policy,
        warnings=["verify_warning", "self_check_warning"],
    )
    assert contract["release_gate_passed"] is False
    assert contract["failed_checks"] == ["verify"]
    assert contract["warnings_count"] == 2
    assert contract["optimization_action"] == "reject"
    assert contract["optimization_requires_review"] is True
    assert contract["reason_codes"] == [
        "benchmark_average_score_below_threshold",
        "benchmark_pass_rate_below_threshold",
        "blocking_checks_failed",
        "optimization_rejected",
        "optimization_requires_review",
    ]
