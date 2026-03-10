from __future__ import annotations

from typing import TypedDict


class CompositionRequest(TypedDict):
    query: str
    composition_mode: bool
    composition_registry: object | None


class CompositionResolution(TypedDict, total=False):
    contract_version: str
    mode: str
    reason_codes: list[str]
    warnings: list[str]
    diagnostics: dict[str, object]
    step_descriptions: list[str]
    composition_graph: dict[str, object]


def build_composition_request(
    *,
    query: str,
    composition_mode: bool,
    composition_registry: object | None,
) -> CompositionRequest:
    return {
        "query": str(query or "").strip(),
        "composition_mode": bool(composition_mode),
        "composition_registry": composition_registry,
    }


def build_composition_resolution(
    *,
    mode: str,
    reason_codes: list[str] | None = None,
    warnings: list[str] | None = None,
    diagnostics: dict[str, object] | None = None,
    step_descriptions: list[str] | None = None,
    composition_graph: dict[str, object] | None = None,
) -> CompositionResolution:
    normalized_mode = str(mode or "").strip().lower() or "fallback"
    if normalized_mode not in {"disabled", "resolved", "fallback"}:
        normalized_mode = "fallback"
    normalized_reasons = sorted(
        set([str(x or "").strip() for x in list(reason_codes or []) if str(x or "").strip()])
    )
    normalized_warnings = sorted(
        set([str(x or "").strip() for x in list(warnings or []) if str(x or "").strip()])
    )
    normalized_steps = [str(x or "").strip() for x in list(step_descriptions or []) if str(x or "").strip()]
    return {
        "contract_version": "v1",
        "mode": normalized_mode,
        "reason_codes": normalized_reasons,
        "warnings": normalized_warnings,
        "diagnostics": dict(diagnostics or {}),
        "step_descriptions": normalized_steps,
        "composition_graph": dict(composition_graph or {}) if composition_graph else None,
    }
