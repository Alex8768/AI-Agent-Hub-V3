from __future__ import annotations

from src.layers.pro.reasoning.enterprise.required_checks_normalizer import (
    normalize_enterprise_required_checks_by_profile,
)


def test_normalize_required_checks_from_github_workflow_jobs():
    payload = {
        "jobs": {
            "release-gate": {"name": "ubuntu-latest / py3.12 / release-gate"},
            "interface-gate": {"name": "ubuntu-latest / node20 / interface-gate"},
            "search-boundary-gate": {"name": "ubuntu-latest / py3.12 / search-boundary-gate"},
        }
    }
    result = normalize_enterprise_required_checks_by_profile(
        workflow_definitions=payload,
        aliases={
            "release_gate": ["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
            "interface_gate": ["ui_quality_gate"],
            "search_boundary_gate": ["search_contract_quality"],
        },
    )
    assert result == {
        "enterprise_default": [
            "reasoning_benchmark",
            "reasoning_optimization",
            "search_contract_quality",
            "self_check",
            "ui_quality_gate",
            "verify",
        ]
    }


def test_normalize_required_checks_from_branch_protection_contexts():
    payload = {
        "required_status_checks": {
            "contexts": [
                " release-gate ",
                "interface-gate",
                "search-boundary-gate",
            ]
        }
    }
    result = normalize_enterprise_required_checks_by_profile(
        workflow_definitions=payload,
        aliases={
            "release_gate": ["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
            "interface_gate": ["ui_quality_gate"],
            "search_boundary_gate": ["search_contract_quality"],
        },
    )
    assert result == {
        "enterprise_default": [
            "reasoning_benchmark",
            "reasoning_optimization",
            "search_contract_quality",
            "self_check",
            "ui_quality_gate",
            "verify",
        ]
    }


def test_normalize_required_checks_supports_profile_mapping():
    payload = {
        "by_profile": {
            "enterprise_default": {
                "required_checks": ["verify", "self-check", "reasoning benchmark"],
            },
            "enterprise_relaxed": "verify, self-check",
        }
    }
    result = normalize_enterprise_required_checks_by_profile(workflow_definitions=payload)
    assert result == {
        "enterprise_default": ["reasoning_benchmark", "self_check", "verify"],
        "enterprise_relaxed": ["self_check", "verify"],
    }
