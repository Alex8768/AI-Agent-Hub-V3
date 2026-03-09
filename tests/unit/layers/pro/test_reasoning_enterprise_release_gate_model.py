from __future__ import annotations

from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
    build_enterprise_release_gate_policy_from_dict,
)


def test_build_enterprise_release_gate_policy_defaults():
    policy = build_enterprise_release_gate_policy()
    assert policy == {
        "profile_name": "default",
        "required_checks": [],
        "blocking_checks": [],
        "minimum_pass_rate": 0.9,
        "minimum_average_score": 0.8,
        "allow_skipped": False,
        "require_benchmark_summary": True,
        "require_optimization_review": True,
        "allowed_warning_codes": [],
    }


def test_build_enterprise_release_gate_policy_normalizes_values():
    policy = build_enterprise_release_gate_policy(
        profile_name=" prod ",
        required_checks=[" ci/test ", "ci/lint", "ci/test"],
        blocking_checks=[],
        minimum_pass_rate="1.4",
        minimum_average_score="-2",
        allow_skipped=1,
        require_benchmark_summary=0,
        require_optimization_review=True,
        allowed_warning_codes=["warn_b", " warn_a ", "warn_a"],
    )
    assert policy == {
        "profile_name": "prod",
        "required_checks": ["ci/lint", "ci/test"],
        "blocking_checks": ["ci/lint", "ci/test"],
        "minimum_pass_rate": 1.0,
        "minimum_average_score": 0.0,
        "allow_skipped": True,
        "require_benchmark_summary": False,
        "require_optimization_review": True,
        "allowed_warning_codes": ["warn_a", "warn_b"],
    }


def test_build_enterprise_release_gate_policy_from_dict_parses_payload():
    policy = build_enterprise_release_gate_policy_from_dict(
        {
            "profile_name": "staging",
            "required_checks": ["check_a", "check_b"],
            "blocking_checks": ["check_a"],
            "minimum_pass_rate": 0.95,
            "minimum_average_score": 0.9,
            "allow_skipped": False,
            "require_benchmark_summary": True,
            "require_optimization_review": False,
            "allowed_warning_codes": ["non_blocking_flake"],
        }
    )
    assert policy["profile_name"] == "staging"
    assert policy["required_checks"] == ["check_a", "check_b"]
    assert policy["blocking_checks"] == ["check_a"]
    assert policy["minimum_pass_rate"] == 0.95
    assert policy["minimum_average_score"] == 0.9
    assert policy["allow_skipped"] is False
    assert policy["require_benchmark_summary"] is True
    assert policy["require_optimization_review"] is False
    assert policy["allowed_warning_codes"] == ["non_blocking_flake"]
