from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.decision_engine import (
    build_tool_safety_decision,
    build_tool_safety_decisions,
)
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


def test_build_tool_safety_decision_allows_allowlisted_tool():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=[],
        allow_network=False,
    )
    decision = build_tool_safety_decision(
        tool_name="search",
        policy=policy,
        catalog=_sample_catalog(),
    )
    assert decision["allowed"] is True
    assert decision["reason"] == "allowed"
    assert decision["violated_constraints"] == []


def test_build_tool_safety_decision_denies_non_allowlisted_tool():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=[],
        allow_network=True,
    )
    decision = build_tool_safety_decision(
        tool_name="shell",
        policy=policy,
        catalog=_sample_catalog(),
    )
    assert decision["allowed"] is False
    assert decision["reason"] == "tool_not_allowlisted"
    assert decision["violated_constraints"] == ["tool_not_allowlisted"]


def test_build_tool_safety_decision_denied_list_has_priority():
    policy = build_tool_safety_sandbox_policy(
        mode="allow_by_default",
        allowed_tools=["shell"],
        denied_tools=["shell"],
    )
    decision = build_tool_safety_decision(
        tool_name="shell",
        policy=policy,
        catalog=_sample_catalog(),
    )
    assert decision["allowed"] is False
    assert "tool_explicitly_denied" in decision["violated_constraints"]


def test_build_tool_safety_decision_respects_network_requirement():
    policy = build_tool_safety_sandbox_policy(
        mode="allow_by_default",
        allowed_tools=[],
        denied_tools=[],
        allow_network=False,
    )
    decision = build_tool_safety_decision(
        tool_name="web",
        policy=policy,
        catalog=_sample_catalog(),
    )
    assert decision["allowed"] is False
    assert decision["reason"] == "network_required_but_disabled"


def test_build_tool_safety_decisions_is_deterministic():
    policy = build_tool_safety_sandbox_policy(
        mode="deny_by_default",
        allowed_tools=["search"],
        denied_tools=["shell"],
        allow_network=False,
    )
    catalog = _sample_catalog()
    a = build_tool_safety_decisions(
        tool_names=["search", "web", "shell"],
        policy=policy,
        catalog=catalog,
    )
    b = build_tool_safety_decisions(
        tool_names=["search", "web", "shell"],
        policy=policy,
        catalog=catalog,
    )
    assert a == b
