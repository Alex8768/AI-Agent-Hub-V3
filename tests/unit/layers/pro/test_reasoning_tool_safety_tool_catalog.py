from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.tool_catalog import (
    build_tool_catalog,
    build_tool_catalog_entry,
)


def test_build_tool_catalog_entry_defaults():
    entry = build_tool_catalog_entry(tool_name="search")
    assert entry == {
        "tool_name": "search",
        "risk_level": "medium",
        "capabilities": ["read"],
        "requires_network": False,
        "requires_filesystem": True,
        "requires_execution": False,
    }


def test_build_tool_catalog_entry_normalizes_values():
    entry = build_tool_catalog_entry(
        tool_name=" shell ",
        risk_level=" HIGH ",
        capabilities=[" Execute ", "read", "execute", ""],
        requires_network="1",
        requires_filesystem="0",
        requires_execution="true",
    )
    assert entry == {
        "tool_name": "shell",
        "risk_level": "high",
        "capabilities": ["execute", "read"],
        "requires_network": True,
        "requires_filesystem": False,
        "requires_execution": True,
    }


def test_build_tool_catalog_entry_unknown_risk_falls_back():
    entry = build_tool_catalog_entry(tool_name="x", risk_level="unsafe")
    assert entry["risk_level"] == "medium"


def test_build_tool_catalog_is_deterministic_and_skips_empty_names():
    catalog = build_tool_catalog(
        rows=[
            {
                "tool_name": "write",
                "risk_level": "high",
                "capabilities": ["write"],
            },
            {
                "tool_name": " ",
                "risk_level": "low",
                "capabilities": ["read"],
            },
            {
                "tool_name": "read",
                "risk_level": "low",
                "capabilities": ["read", "read"],
            },
        ]
    )
    assert [row["tool_name"] for row in catalog] == ["read", "write"]
    assert catalog[0]["capabilities"] == ["read"]
