from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.evaluation.benchmark_model import (
    ReasoningBenchmarkCase,
    build_reasoning_benchmark_case,
)


class ReasoningBenchmarkSuite(TypedDict):
    suite_name: str
    cases: list[ReasoningBenchmarkCase]
    tags: list[str]
    owner: str


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    normalized: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            normalized.append(item)
    return sorted(set(normalized))


def build_reasoning_benchmark_suite(
    *,
    suite_name: object,
    cases: list[dict[str, object]],
    tags: object = None,
    owner: object = "",
) -> ReasoningBenchmarkSuite:
    """Build deterministic benchmark suite contract."""
    normalized_cases: list[ReasoningBenchmarkCase] = []
    for raw in list(cases or []):
        row = raw if isinstance(raw, dict) else {}
        case = build_reasoning_benchmark_case(
            case_id=row.get("case_id", ""),
            query=row.get("query", ""),
            expected_signals=row.get("expected_signals", []),
            tags=row.get("tags", []),
            weight=row.get("weight", 1.0),
        )
        if not case["case_id"] or not case["query"]:
            continue
        normalized_cases.append(case)
    normalized_cases.sort(key=lambda x: str(x["case_id"]))
    return {
        "suite_name": _normalize_string(suite_name),
        "cases": normalized_cases,
        "tags": _normalize_string_list(tags),
        "owner": _normalize_string(owner),
    }


def build_reasoning_benchmark_registry(
    *,
    suites: list[dict[str, object]],
) -> list[ReasoningBenchmarkSuite]:
    """Build deterministic benchmark suite registry."""
    normalized_suites: list[ReasoningBenchmarkSuite] = []
    for raw in list(suites or []):
        row = raw if isinstance(raw, dict) else {}
        suite = build_reasoning_benchmark_suite(
            suite_name=row.get("suite_name", ""),
            cases=list(row.get("cases") or []),
            tags=row.get("tags", []),
            owner=row.get("owner", ""),
        )
        if not suite["suite_name"]:
            continue
        normalized_suites.append(suite)
    normalized_suites.sort(key=lambda x: str(x["suite_name"]))
    return normalized_suites
