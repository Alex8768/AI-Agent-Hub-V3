from __future__ import annotations

from src.layers.pro.reasoning.evaluation.benchmark_registry import (
    build_reasoning_benchmark_registry,
    build_reasoning_benchmark_suite,
)


def test_build_reasoning_benchmark_suite_normalizes_and_filters_cases():
    suite = build_reasoning_benchmark_suite(
        suite_name=" smoke ",
        owner=" team-ai ",
        tags=["core", " core ", "reasoning"],
        cases=[
            {
                "case_id": " b ",
                "query": " second ",
                "expected_signals": ["source_refs", "source_refs"],
                "tags": ["qa"],
                "weight": "0.5",
            },
            {
                "case_id": "a",
                "query": " first ",
                "expected_signals": ["confidence"],
                "tags": [],
                "weight": 1.0,
            },
            {
                "case_id": "drop",
                "query": " ",
                "expected_signals": [],
                "tags": [],
                "weight": 1.0,
            },
        ],
    )
    assert suite["suite_name"] == "smoke"
    assert suite["owner"] == "team-ai"
    assert suite["tags"] == ["core", "reasoning"]
    assert [x["case_id"] for x in suite["cases"]] == ["a", "b"]


def test_build_reasoning_benchmark_registry_is_deterministic():
    registry = build_reasoning_benchmark_registry(
        suites=[
            {
                "suite_name": "beta",
                "owner": "b",
                "tags": ["regression"],
                "cases": [{"case_id": "c1", "query": "q1"}],
            },
            {
                "suite_name": "alpha",
                "owner": "a",
                "tags": ["smoke"],
                "cases": [{"case_id": "c2", "query": "q2"}],
            },
            {
                "suite_name": " ",
                "owner": "x",
                "tags": [],
                "cases": [{"case_id": "c3", "query": "q3"}],
            },
        ]
    )
    assert [x["suite_name"] for x in registry] == ["alpha", "beta"]
