from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.trace.trace_model import ReasoningTrace, build_reasoning_trace


def _extract_plan_descriptions(plan: dict[str, Any]) -> list[str]:
    steps = list(plan.get("steps") or [])
    descriptions: list[str] = []
    for raw in steps:
        step = raw if isinstance(raw, dict) else {}
        descriptions.append(str(step.get("description", "") or ""))
    return descriptions


def _extract_reasoning_outputs(step_results: list[dict[str, Any]]) -> list[str]:
    outputs: list[str] = []
    for raw in step_results:
        row = raw if isinstance(raw, dict) else {}
        outputs.append(str(row.get("reasoning_output", "") or ""))
    return outputs


def _extract_verify_results(step_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verify_results: list[dict[str, Any]] = []
    for raw in step_results:
        row = raw if isinstance(raw, dict) else {}
        verify_results.append(
            {
                "status": row.get("verify_status", ""),
                "reasons": list(row.get("verify_reasons") or []),
            }
        )
    return verify_results


def collect_reasoning_trace(
    *,
    query: str,
    plan: dict[str, Any],
    step_results: list[dict[str, Any]],
    quality: dict[str, Any],
    answer: str,
) -> ReasoningTrace:
    """Collect trace payload from planner outputs and quality diagnostics."""
    return build_reasoning_trace(
        query=query,
        plan=_extract_plan_descriptions(plan),
        steps=_extract_reasoning_outputs(step_results),
        verify_results=_extract_verify_results(step_results),
        quality=dict(quality or {}),
        answer=answer,
    )
