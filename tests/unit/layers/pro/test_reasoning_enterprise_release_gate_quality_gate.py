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
from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    build_enterprise_required_checks_policy,
    evaluate_enterprise_required_checks,
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


def _required_checks_policy():
    return build_enterprise_required_checks_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        stable_statuses=["pass"],
        treat_missing_as_failure=True,
        allow_warnings=False,
    )


def _diagnostics_pass() -> dict[str, object]:
    return {
        "verify": {"status": "pass"},
        "self_check": {"status": "pass"},
        "reasoning_benchmark": {
            "summary": {
                "suite_name": "enterprise-gate",
                "total_cases": 12,
                "passed_cases": 11,
                "pass_rate": 0.916,
                "average_score": 0.9,
            }
        },
        "coverage": {"line_rate": 0.9},
        "reasoning_optimization": {
            "decision": {"action": "approve", "requires_human_review": False}
        },
    }


def test_release_gate_quality_gate_chain_is_deterministic():
    diagnostics = _diagnostics_pass()
    checks_policy = _required_checks_policy()
    gate_policy = _policy()
    run_a_inputs = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
        required_checks_policy=checks_policy,
    )
    run_b_inputs = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
        required_checks_policy=checks_policy,
    )
    assert run_a_inputs == run_b_inputs

    run_a_decision = decide_enterprise_release_gate(
        inputs=run_a_inputs,
        policy=gate_policy,
        decision_id="release_gate:qg",
    )
    run_b_decision = decide_enterprise_release_gate(
        inputs=run_b_inputs,
        policy=gate_policy,
        decision_id="release_gate:qg",
    )
    assert run_a_decision == run_b_decision


def test_release_gate_quality_gate_parity_with_required_checks_evaluation():
    diagnostics = _diagnostics_pass()
    checks_policy = _required_checks_policy()
    inputs = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
        required_checks_policy=checks_policy,
    )
    direct = evaluate_enterprise_required_checks(
        policy=checks_policy,
        check_states=inputs["release_checks"],
    )
    assert inputs["required_checks_evaluation"] == direct


def test_release_gate_quality_gate_fail_safe_missing_benchmark_summary():
    diagnostics = {
        "verify": {"status": "pass"},
        "self_check": {"status": "pass"},
        "reasoning_optimization": {
            "decision": {"action": "approve", "requires_human_review": False}
        },
    }
    inputs = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
        required_checks_policy=_required_checks_policy(),
    )
    decision = decide_enterprise_release_gate(
        inputs=inputs,
        policy=_policy(),
        decision_id="release_gate:missing_benchmark",
    )
    assert decision["status"] == "fail"
    assert decision["recommended_action"] == "block"
    assert "benchmark_summary_missing" in decision["reason_codes"]
