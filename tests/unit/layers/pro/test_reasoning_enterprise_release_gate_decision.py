from __future__ import annotations

from src.layers.pro.reasoning.enterprise.release_gate_aggregator import (
    build_enterprise_release_gate_inputs,
)
from src.layers.pro.reasoning.enterprise.release_gate_decision import (
    decide_enterprise_release_gate,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)


def _policy():
    return build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        minimum_coverage_ratio=0.8,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )


def test_decide_enterprise_release_gate_is_deterministic():
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={
            "verify": {"status": "pass"},
            "self_check": {"status": "pass"},
            "reasoning_benchmark": {
                "summary": {"suite_name": "s", "total_cases": 10, "passed_cases": 9, "pass_rate": 0.9, "average_score": 0.85}
            },
            "coverage": {"line_rate": 0.9},
            "reasoning_optimization": {"decision": {"action": "approve", "requires_human_review": False}},
        },
        warnings=[],
        profile_name="enterprise_default",
    )
    run_a = decide_enterprise_release_gate(inputs=inputs, policy=_policy(), decision_id="gate:1")
    run_b = decide_enterprise_release_gate(inputs=inputs, policy=_policy(), decision_id="gate:1")
    assert run_a == run_b


def test_decide_enterprise_release_gate_fails_on_thresholds_and_blocking_checks():
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={
            "verify": {"status": "warn"},
            "self_check": {"status": "pass"},
            "reasoning_benchmark": {
                "summary": {"suite_name": "s", "total_cases": 5, "passed_cases": 2, "pass_rate": 0.4, "average_score": 0.5}
            },
            "coverage": {"line_rate": 0.5},
            "reasoning_optimization": {"decision": {"action": "approve", "requires_human_review": False}},
        },
        warnings=[],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(inputs=inputs, policy=_policy(), decision_id="gate:fail")
    assert decision["status"] == "fail"
    assert decision["recommended_action"] == "block"
    assert "required_checks_failed" in decision["reason_codes"]
    assert "benchmark_pass_rate_below_threshold" in decision["reason_codes"]
    assert "benchmark_average_score_below_threshold" in decision["reason_codes"]
    assert "coverage_ratio_below_threshold" in decision["reason_codes"]
    assert decision["blocking_checks"] == ["verify"]


def test_decide_enterprise_release_gate_warns_when_review_required():
    policy = build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        minimum_coverage_ratio=0.8,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={
            "verify": {"status": "pass"},
            "self_check": {"status": "pass"},
            "reasoning_benchmark": {
                "summary": {"suite_name": "s", "total_cases": 10, "passed_cases": 9, "pass_rate": 0.9, "average_score": 0.9}
            },
            "coverage": {"line_rate": 0.92},
            "reasoning_optimization": {"decision": {"action": "defer", "requires_human_review": True}},
        },
        warnings=["minor_warning"],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(inputs=inputs, policy=policy, decision_id="gate:warn")
    assert decision["status"] == "warn"
    assert decision["recommended_action"] == "hold"
    assert "optimization_review_required" in decision["reason_codes"]
    assert "warnings_present" in decision["reason_codes"]


def test_decide_enterprise_release_gate_fails_when_coverage_missing_and_required():
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={
            "verify": {"status": "pass"},
            "self_check": {"status": "pass"},
            "reasoning_benchmark": {
                "summary": {"suite_name": "s", "total_cases": 10, "passed_cases": 9, "pass_rate": 0.9, "average_score": 0.9}
            },
            "reasoning_optimization": {"decision": {"action": "approve", "requires_human_review": False}},
        },
        warnings=[],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(inputs=inputs, policy=_policy(), decision_id="gate:coverage_missing")
    assert decision["status"] == "fail"
    assert "coverage_summary_missing" in decision["reason_codes"]
