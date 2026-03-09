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


def _policy() -> dict[str, object]:
    return build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        minimum_coverage_ratio=0.85,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )


def _diagnostics_base() -> dict[str, object]:
    return {
        "verify": {"status": "pass"},
        "self_check": {"status": "pass"},
        "reasoning_benchmark": {
            "summary": {
                "suite_name": "coverage-gate",
                "total_cases": 10,
                "passed_cases": 9,
                "pass_rate": 0.9,
                "average_score": 0.9,
            }
        },
        "reasoning_optimization": {
            "decision": {"action": "approve", "requires_human_review": False}
        },
    }


def test_release_gate_coverage_quality_gate_is_deterministic() -> None:
    diagnostics = {**_diagnostics_base(), "coverage": {"line_rate": 0.9}}
    inputs_a = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
    )
    inputs_b = build_enterprise_release_gate_inputs(
        diagnostics=diagnostics,
        warnings=[],
        profile_name="enterprise_default",
    )
    assert inputs_a == inputs_b

    run_a = decide_enterprise_release_gate(
        inputs=inputs_a,
        policy=_policy(),
        decision_id="coverage_gate:qg",
    )
    run_b = decide_enterprise_release_gate(
        inputs=inputs_b,
        policy=_policy(),
        decision_id="coverage_gate:qg",
    )
    assert run_a == run_b


def test_release_gate_coverage_quality_gate_fail_safe_when_missing() -> None:
    inputs = build_enterprise_release_gate_inputs(
        diagnostics=_diagnostics_base(),
        warnings=[],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(
        inputs=inputs,
        policy=_policy(),
        decision_id="coverage_gate:missing",
    )
    assert decision["status"] == "fail"
    assert decision["recommended_action"] == "block"
    assert "coverage_summary_missing" in decision["reason_codes"]


def test_release_gate_coverage_quality_gate_fails_below_threshold() -> None:
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={**_diagnostics_base(), "coverage": {"line_rate": 0.8}},
        warnings=[],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(
        inputs=inputs,
        policy=_policy(),
        decision_id="coverage_gate:below",
    )
    assert decision["status"] == "fail"
    assert decision["recommended_action"] == "block"
    assert "coverage_ratio_below_threshold" in decision["reason_codes"]


def test_release_gate_coverage_quality_gate_passes_at_threshold() -> None:
    inputs = build_enterprise_release_gate_inputs(
        diagnostics={**_diagnostics_base(), "coverage": {"coverage_percent": 85}},
        warnings=[],
        profile_name="enterprise_default",
    )
    decision = decide_enterprise_release_gate(
        inputs=inputs,
        policy=_policy(),
        decision_id="coverage_gate:at_threshold",
    )
    assert decision["status"] == "pass"
    assert decision["recommended_action"] == "promote"
    assert "release_gate_passed" in decision["reason_codes"]
