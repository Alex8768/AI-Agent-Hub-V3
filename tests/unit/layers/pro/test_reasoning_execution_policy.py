from __future__ import annotations

from src.layers.pro.reasoning.control.execution_policy import (
    build_reasoning_execution_policy,
    build_reasoning_execution_policy_from_dict,
)


def test_build_reasoning_execution_policy_uses_defaults():
    policy = build_reasoning_execution_policy()
    assert policy == {
        "max_steps": 3,
        "max_latency_ms": 15000,
        "max_retries": 1,
    }


def test_build_reasoning_execution_policy_keeps_explicit_values():
    policy = build_reasoning_execution_policy(
        max_steps=7,
        max_latency_ms=23000,
        max_retries=2,
    )
    assert policy == {
        "max_steps": 7,
        "max_latency_ms": 23000,
        "max_retries": 2,
    }


def test_build_reasoning_execution_policy_normalizes_bounds():
    policy = build_reasoning_execution_policy(
        max_steps=-1,
        max_latency_ms=0,
        max_retries=-10,
    )
    assert policy == {
        "max_steps": 1,
        "max_latency_ms": 1,
        "max_retries": 0,
    }


def test_build_reasoning_execution_policy_applies_caps():
    policy = build_reasoning_execution_policy(
        max_steps=1000,
        max_latency_ms=9999999,
        max_retries=999,
    )
    assert policy == {
        "max_steps": 100,
        "max_latency_ms": 300000,
        "max_retries": 10,
    }


def test_build_reasoning_execution_policy_from_dict_parses_string_inputs():
    policy = build_reasoning_execution_policy_from_dict(
        raw={
            "max_steps": "9",
            "max_latency_ms": "12000",
            "max_retries": "3",
        }
    )
    assert policy == {
        "max_steps": 9,
        "max_latency_ms": 12000,
        "max_retries": 3,
    }
