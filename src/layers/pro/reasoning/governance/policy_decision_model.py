from __future__ import annotations

from typing import TypedDict


class ReasoningPolicyDecision(TypedDict):
    policy_name: str
    status: str
    reason: str


def build_reasoning_policy_decision(
    *,
    policy_name: object,
    status: object,
    reason: object,
) -> ReasoningPolicyDecision:
    """Build normalized policy decision row."""
    return {
        "policy_name": str(policy_name or "").strip(),
        "status": str(status or "").strip(),
        "reason": str(reason or "").strip(),
    }


def build_reasoning_policy_decisions(
    *,
    rows: list[dict[str, object]],
) -> list[ReasoningPolicyDecision]:
    """Build normalized list of policy decisions and skip empty rows."""
    normalized: list[ReasoningPolicyDecision] = []
    for raw in list(rows or []):
        item = raw if isinstance(raw, dict) else {}
        decision = build_reasoning_policy_decision(
            policy_name=item.get("policy_name", ""),
            status=item.get("status", ""),
            reason=item.get("reason", ""),
        )
        if (
            not decision["policy_name"]
            and not decision["status"]
            and not decision["reason"]
        ):
            continue
        normalized.append(decision)
    return normalized
