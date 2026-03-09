from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.sandbox_policy import (
    build_tool_safety_sandbox_policy,
    build_tool_safety_sandbox_policy_from_dict,
)


def test_build_tool_safety_sandbox_policy_defaults():
    policy = build_tool_safety_sandbox_policy()
    assert policy == {
        "mode": "deny_by_default",
        "allowed_tools": ["search"],
        "denied_tools": ["shell"],
        "allowed_path_prefixes": ["/workspace"],
        "allow_network": False,
        "max_execution_seconds": 30,
    }


def test_build_tool_safety_sandbox_policy_normalizes_values():
    policy = build_tool_safety_sandbox_policy(
        mode=" allow_by_default ",
        allowed_tools=[" search ", "", "shell", "search"],
        denied_tools=[" shell ", "shell", "python"],
        allowed_path_prefixes=["/tmp", " /workspace ", "", "/workspace"],
        allow_network="true",
        max_execution_seconds="999",
    )
    assert policy == {
        "mode": "allow_by_default",
        "allowed_tools": ["search", "shell"],
        "denied_tools": ["python", "shell"],
        "allowed_path_prefixes": ["/tmp", "/workspace"],
        "allow_network": True,
        "max_execution_seconds": 600,
    }


def test_build_tool_safety_sandbox_policy_rejects_unknown_mode():
    policy = build_tool_safety_sandbox_policy(mode="custom")
    assert policy["mode"] == "deny_by_default"


def test_build_tool_safety_sandbox_policy_from_dict_accepts_string_inputs():
    policy = build_tool_safety_sandbox_policy_from_dict(
        raw={
            "mode": "allow_by_default",
            "allowed_tools": ["read", "write", "read"],
            "denied_tools": ["shell"],
            "allowed_path_prefixes": ["/workspace/project"],
            "allow_network": "0",
            "max_execution_seconds": "45",
        }
    )
    assert policy == {
        "mode": "allow_by_default",
        "allowed_tools": ["read", "write"],
        "denied_tools": ["shell"],
        "allowed_path_prefixes": ["/workspace/project"],
        "allow_network": False,
        "max_execution_seconds": 45,
    }
