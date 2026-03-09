from __future__ import annotations

from src.layers.pro.reasoning.enterprise.release_gate_aggregator import (
    build_enterprise_release_gate_inputs,
)
from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    build_enterprise_required_checks_policy,
    evaluate_enterprise_required_checks,
)


def _diagnostics_payload() -> dict[str, object]:
    return {
        "verify": {"status": "pass"},
        "self_check": {"status": "warn"},
        "reasoning_benchmark": {
            "summary": {
                "suite_name": "reasoning-smoke",
                "total_cases": 10,
                "passed_cases": 8,
                "pass_rate": 0.8,
                "average_score": 0.81,
            }
        },
        "coverage": {"line_rate": 0.86},
        "reasoning_optimization": {
            "decision": {
                "action": "approve",
                "requires_human_review": False,
            }
        },
    }


def test_build_enterprise_release_gate_inputs_is_deterministic():
    diag = _diagnostics_payload()
    run_a = build_enterprise_release_gate_inputs(
        diagnostics=diag,
        warnings=["warn_b", " warn_a ", "warn_a"],
        profile_name=" prod ",
    )
    run_b = build_enterprise_release_gate_inputs(
        diagnostics=diag,
        warnings=["warn_b", " warn_a ", "warn_a"],
        profile_name=" prod ",
    )
    assert run_a == run_b


def test_build_enterprise_release_gate_inputs_normalizes_contract_shape():
    payload = build_enterprise_release_gate_inputs(
        diagnostics=_diagnostics_payload(),
        warnings=[" warn_x ", "warn_x"],
        profile_name="prod",
    )
    assert set(payload.keys()) == {
        "profile_name",
        "release_checks",
        "benchmark_summary",
        "coverage_ratio",
        "optimization_decision",
        "warnings",
        "warnings_count",
        "required_checks_evaluation",
    }
    assert payload["profile_name"] == "prod"
    assert payload["warnings"] == ["warn_x"]
    assert payload["warnings_count"] == 1
    assert payload["release_checks"]["verify"] == "pass"
    assert payload["release_checks"]["self_check"] == "warn"
    assert payload["benchmark_summary"]["pass_rate"] == 0.8
    assert payload["coverage_ratio"] == 0.86
    assert payload["optimization_decision"]["action"] == "approve"


def test_build_enterprise_release_gate_inputs_parity_with_required_checks_evaluator():
    policy = build_enterprise_required_checks_policy(
        profile_name="prod",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        stable_statuses=["pass"],
        treat_missing_as_failure=True,
        allow_warnings=False,
    )
    payload = build_enterprise_release_gate_inputs(
        diagnostics=_diagnostics_payload(),
        warnings=[],
        profile_name="prod",
        required_checks_policy=policy,
    )
    direct = evaluate_enterprise_required_checks(
        policy=policy,
        check_states=payload["release_checks"],
    )
    assert payload["required_checks_evaluation"] == direct
