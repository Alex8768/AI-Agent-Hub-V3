from __future__ import annotations

from src.layers.pro.reasoning.enterprise.required_checks_matrix import (
    consolidate_enterprise_required_checks_matrix,
)
from src.layers.pro.reasoning.enterprise.required_checks_policy import (
    build_enterprise_required_checks_policy,
)


def _policies():
    return [
        build_enterprise_required_checks_policy(
            profile_name="enterprise_default",
            required_checks=["verify", "self_check"],
            stable_statuses=["pass"],
            treat_missing_as_failure=True,
            allow_warnings=False,
        ),
        build_enterprise_required_checks_policy(
            profile_name="enterprise_relaxed",
            required_checks=["verify"],
            stable_statuses=["pass", "warn"],
            treat_missing_as_failure=True,
            allow_warnings=True,
        ),
    ]


def test_required_checks_consolidation_is_deterministic():
    workflow_by_profile = {
        "enterprise_default": ["reasoning_benchmark", "self_check"],
        "enterprise_relaxed": ["ui_quality_gate"],
    }
    run_a = consolidate_enterprise_required_checks_matrix(
        policies=_policies(),
        workflow_required_checks_by_profile=workflow_by_profile,
        blocking_checks_by_profile={"enterprise_default": ["verify", "self_check"]},
        version=" v1 ",
    )
    run_b = consolidate_enterprise_required_checks_matrix(
        policies=_policies(),
        workflow_required_checks_by_profile=workflow_by_profile,
        blocking_checks_by_profile={"enterprise_default": ["verify", "self_check"]},
        version=" v1 ",
    )
    assert run_a == run_b


def test_required_checks_consolidation_merges_policy_and_workflow_checks():
    payload = consolidate_enterprise_required_checks_matrix(
        policies=_policies(),
        workflow_required_checks_by_profile={
            "enterprise_default": ["reasoning_benchmark"],
            "enterprise_relaxed": ["ui_quality_gate"],
        },
        blocking_checks_by_profile={"enterprise_default": ["verify"]},
    )
    assert [x["profile_name"] for x in payload["profiles"]] == [
        "enterprise_default",
        "enterprise_relaxed",
    ]
    default_profile = payload["profiles"][0]
    assert default_profile["required_checks"] == ["reasoning_benchmark", "self_check", "verify"]
    assert default_profile["blocking_checks"] == ["verify"]
    relaxed_profile = payload["profiles"][1]
    assert relaxed_profile["required_checks"] == ["ui_quality_gate", "verify"]
    assert relaxed_profile["blocking_checks"] == ["ui_quality_gate", "verify"]


def test_required_checks_consolidation_adds_missing_profile_from_workflow():
    payload = consolidate_enterprise_required_checks_matrix(
        policies=[],
        workflow_required_checks_by_profile={"enterprise_ci_only": ["release_gate", "interface_gate"]},
    )
    assert [x["profile_name"] for x in payload["profiles"]] == ["enterprise_ci_only"]
    profile = payload["profiles"][0]
    assert profile["required_checks"] == ["interface_gate", "release_gate"]
    assert profile["stable_statuses"] == ["pass"]
    assert profile["treat_missing_as_failure"] is True
    assert profile["allow_warnings"] is False
