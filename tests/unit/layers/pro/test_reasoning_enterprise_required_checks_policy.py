from __future__ import annotations

from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    build_enterprise_required_checks_policy,
    evaluate_enterprise_required_checks,
)


def test_build_enterprise_required_checks_policy_normalizes_values():
    policy = build_enterprise_required_checks_policy(
        profile_name=" prod ",
        required_checks=["ci/test", " ci/lint ", "ci/test"],
        stable_statuses=[" pass ", "PASS", "missing"],
        treat_missing_as_failure=1,
        allow_warnings=0,
    )
    assert policy == {
        "profile_name": "prod",
        "required_checks": ["ci/lint", "ci/test"],
        "stable_statuses": ["pass"],
        "treat_missing_as_failure": True,
        "allow_warnings": False,
    }


def test_evaluate_enterprise_required_checks_fails_on_missing_and_unstable():
    policy = build_enterprise_required_checks_policy(
        profile_name="prod",
        required_checks=["ci/lint", "ci/test", "ci/security"],
        stable_statuses=["pass"],
        treat_missing_as_failure=True,
        allow_warnings=False,
    )
    evaluation = evaluate_enterprise_required_checks(
        policy=policy,
        check_states={"ci/lint": "pass", "ci/test": "warn"},
    )
    assert evaluation["passed"] is False
    assert evaluation["failed_checks"] == ["ci/security", "ci/test"]
    assert evaluation["missing_checks"] == ["ci/security"]
    assert evaluation["unstable_checks"] == []
    assert evaluation["reason_codes"] == ["required_check_missing", "required_check_not_stable"]


def test_evaluate_enterprise_required_checks_allows_warn_when_configured():
    policy = build_enterprise_required_checks_policy(
        profile_name="prod",
        required_checks=["ci/lint", "ci/test"],
        stable_statuses=["pass"],
        treat_missing_as_failure=True,
        allow_warnings=True,
    )
    evaluation = evaluate_enterprise_required_checks(
        policy=policy,
        check_states={"ci/lint": "pass", "ci/test": "warn"},
    )
    assert evaluation["passed"] is True
    assert evaluation["failed_checks"] == []
    assert evaluation["unstable_checks"] == ["ci/test"]
    assert evaluation["reason_codes"] == ["warning_status_present"]
