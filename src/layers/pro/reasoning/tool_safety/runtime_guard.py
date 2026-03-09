from __future__ import annotations

from src.layers.pro.reasoning.tool_safety.decision_engine import build_tool_safety_decision
from src.layers.pro.reasoning.tool_safety.sandbox_policy import (
    ToolSafetySandboxPolicy,
    build_tool_safety_sandbox_policy,
)
from src.layers.pro.reasoning.tool_safety.tool_catalog import (
    ToolCatalogEntry,
    build_tool_catalog,
)


def _infer_tool_name(step_description: object) -> str:
    text = str(step_description or "").strip().lower()
    if any(x in text for x in ("shell", "bash", "terminal", "command")):
        return "shell"
    if any(x in text for x in ("web", "http", "url", "browser")):
        return "web"
    if any(x in text for x in ("write", "save", "file")):
        return "write"
    if any(x in text for x in ("read", "load", "open")):
        return "read"
    return "search"


def _default_catalog() -> list[ToolCatalogEntry]:
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
            {
                "tool_name": "write",
                "risk_level": "high",
                "capabilities": ["write"],
                "requires_network": False,
                "requires_filesystem": True,
                "requires_execution": False,
            },
            {
                "tool_name": "read",
                "risk_level": "low",
                "capabilities": ["read"],
                "requires_network": False,
                "requires_filesystem": True,
                "requires_execution": False,
            },
        ]
    )


def apply_tool_safety_runtime_guard(
    *,
    step_results: list[dict[str, object]],
    policy: ToolSafetySandboxPolicy | None = None,
    catalog: list[ToolCatalogEntry] | None = None,
) -> list[dict[str, object]]:
    """Enrich runtime step rows with deterministic tool safety decision."""
    active_policy = policy if policy is not None else build_tool_safety_sandbox_policy()
    active_catalog = list(catalog or _default_catalog())

    guarded: list[dict[str, object]] = []
    for raw in list(step_results or []):
        row = dict(raw or {})
        inferred_tool = _infer_tool_name(row.get("step_description", ""))
        decision = build_tool_safety_decision(
            tool_name=inferred_tool,
            policy=active_policy,
            catalog=active_catalog,
        )
        blocked = not bool(decision.get("allowed", False))
        row["tool_safety_decision"] = dict(decision)
        row["tool_safety_blocked"] = blocked
        if blocked:
            reasons = [str(x) for x in list(row.get("verify_reasons") or [])]
            reasons.append(f"tool_safety:{str(decision.get('reason', '') or '')}")
            row["verify_reasons"] = sorted(set(reasons))
            if str(row.get("verify_status", "") or "") == "pass":
                row["verify_status"] = "warn"
        guarded.append(row)
    return guarded
