from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.decision_engine import (
    build_tool_safety_decision,
    build_tool_safety_decisions,
)
from src.layers.pro.reasoning.tool_safety.runtime_guard import apply_tool_safety_runtime_guard
from src.layers.pro.reasoning.tool_safety.sandbox_policy import (
    build_tool_safety_sandbox_policy,
)
from src.layers.pro.reasoning.tool_safety.tool_catalog import build_tool_catalog


def _sample_catalog():
    return build_tool_catalog(
        rows=[
            {
                "tool_name": "search",
                "risk_level": "low",
                "capabilities": ["read"],
                "requires_network": False,
                "requires_filesystem": False,
                "requires_execution": False,
            },
            {
                "tool_name": "web",
                "risk_level": "high",
                "capabilities": ["read", "network"],
                "requires_network": True,
                "requires_filesystem": False,
                "requires_execution": False,
            },
            {
                "tool_name": "shell",
                "risk_level": "critical",
                "capabilities": ["execute", "write"],
                "requires_network": False,
                "requires_filesystem": True,
                "requires_execution": True,
            },
        ]
    )


def test_tool_safety_quality_gate_decisions_are_deterministic():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=["shell"],
        allow_network=False,
    )
    catalog = _sample_catalog()
    run_a = build_tool_safety_decisions(
        tool_names=["search", "web", "shell"],
        policy=policy,
        catalog=catalog,
    )
    run_b = build_tool_safety_decisions(
        tool_names=["search", "web", "shell"],
        policy=policy,
        catalog=catalog,
    )
    assert run_a == run_b


def test_tool_safety_quality_gate_enforces_policy_boundaries():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=["shell"],
        allow_network=False,
    )
    catalog = _sample_catalog()
    shell_decision = build_tool_safety_decision(
        tool_name="shell",
        policy=policy,
        catalog=catalog,
    )
    web_decision = build_tool_safety_decision(
        tool_name="web",
        policy=policy,
        catalog=catalog,
    )
    search_decision = build_tool_safety_decision(
        tool_name="search",
        policy=policy,
        catalog=catalog,
    )
    assert shell_decision["allowed"] is False
    assert shell_decision["reason"] == "tool_explicitly_denied"
    assert web_decision["allowed"] is False
    assert web_decision["reason"] == "network_required_but_disabled"
    assert search_decision["allowed"] is True
    assert search_decision["reason"] == "allowed"


def test_tool_safety_quality_gate_runtime_guard_contract_parity():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=["shell"],
        allow_network=False,
    )
    rows = apply_tool_safety_runtime_guard(
        step_results=[
            {
                "step_index": 0,
                "step_description": "run shell command",
                "reasoning_output": "x",
                "verify_status": "pass",
                "verify_reasons": [],
            },
            {
                "step_index": 1,
                "step_description": "search knowledge base",
                "reasoning_output": "y",
                "verify_status": "pass",
                "verify_reasons": [],
            },
        ],
        policy=policy,
        catalog=_sample_catalog(),
    )
    assert len(rows) == 2
    step_keys = set(rows[0].keys())
    assert step_keys == set(rows[1].keys())
    assert "tool_safety_decision" in step_keys
    assert "tool_safety_blocked" in step_keys
    decision_keys = set(dict(rows[0]["tool_safety_decision"]).keys())
    assert decision_keys == {
        "tool_name",
        "allowed",
        "reason",
        "mode",
        "risk_level",
        "requires_network",
        "requires_filesystem",
        "requires_execution",
        "violated_constraints",
    }


def test_tool_safety_quality_gate_runtime_guard_matches_decision_engine():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=["shell"],
        allow_network=False,
    )
    catalog = _sample_catalog()
    rows = apply_tool_safety_runtime_guard(
        step_results=[
            {
                "step_index": 0,
                "step_description": "open web url",
                "reasoning_output": "x",
                "verify_status": "pass",
                "verify_reasons": [],
            }
        ],
        policy=policy,
        catalog=catalog,
    )
    runtime_decision = dict(rows[0]["tool_safety_decision"])
    direct_decision = build_tool_safety_decision(
        tool_name="web",
        policy=policy,
        catalog=catalog,
    )
    assert runtime_decision == direct_decision
