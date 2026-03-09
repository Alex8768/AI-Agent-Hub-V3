from __future__ import annotations

from src.layers.pro.reasoning.enterprise.required_checks_matrix import (
    build_enterprise_required_checks_matrix,
)
from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    build_enterprise_required_checks_policy,
)


def _policies():
    return [
        build_enterprise_required_checks_policy(
            profile_name="enterprise_default",
            required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
            stable_statuses=["pass"],
            treat_missing_as_failure=True,
            allow_warnings=False,
        ),
        build_enterprise_required_checks_policy(
            profile_name="enterprise_relaxed",
            required_checks=["verify", "self_check"],
            stable_statuses=["pass", "warn"],
            treat_missing_as_failure=True,
            allow_warnings=True,
        ),
    ]


def test_build_enterprise_required_checks_matrix_is_deterministic():
    run_a = build_enterprise_required_checks_matrix(
        policies=_policies(),
        blocking_checks_by_profile={
            "enterprise_default": ["verify", "self_check"],
            "enterprise_relaxed": ["verify"],
        },
        version=" v1 ",
    )
    run_b = build_enterprise_required_checks_matrix(
        policies=_policies(),
        blocking_checks_by_profile={
            "enterprise_default": ["verify", "self_check"],
            "enterprise_relaxed": ["verify"],
        },
        version=" v1 ",
    )
    assert run_a == run_b


def test_build_enterprise_required_checks_matrix_normalizes_shape():
    payload = build_enterprise_required_checks_matrix(
        policies=_policies(),
        blocking_checks_by_profile={"enterprise_default": ["self_check", "verify", "verify"]},
    )
    assert set(payload.keys()) == {
        "version",
        "profiles",
        "all_required_checks",
        "all_blocking_checks",
    }
    assert payload["version"] == "v1"
    assert [p["profile_name"] for p in payload["profiles"]] == [
        "enterprise_default",
        "enterprise_relaxed",
    ]
    default = payload["profiles"][0]
    assert default["blocking_checks"] == ["self_check", "verify"]
    relaxed = payload["profiles"][1]
    assert relaxed["blocking_checks"] == ["self_check", "verify"]
    assert payload["all_required_checks"] == [
        "reasoning_benchmark",
        "reasoning_optimization",
        "self_check",
        "verify",
    ]
    assert payload["all_blocking_checks"] == ["self_check", "verify"]
