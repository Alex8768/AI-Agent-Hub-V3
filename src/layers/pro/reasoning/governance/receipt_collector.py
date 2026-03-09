from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.governance.policy_decision_model import (
    ReasoningPolicyDecision,
    build_reasoning_policy_decision,
)
from src.layers.pro.reasoning.governance.receipt_model import (
    ReasoningExecutionReceipt,
    build_reasoning_execution_receipt,
)


def _parse_source_row(raw: object, *, default_confidence: float) -> dict[str, object]:
    value = str(raw or "").strip()
    if not value:
        return {}
    if ":" in value:
        prefix, rest = value.split(":", 1)
        source_type = str(prefix or "").strip().lower()
        source_id = str(rest or "").strip()
    else:
        source_type = "unknown"
        source_id = value
    return {
        "source_id": source_id,
        "source_type": source_type,
        "confidence": float(default_confidence),
    }


def _extract_sources(
    *,
    diagnostics: dict[str, Any],
    default_confidence: float,
) -> list[dict[str, object]]:
    rows = list(diagnostics.get("top_evidence") or [])
    sources: list[dict[str, object]] = []
    for raw in rows:
        item = _parse_source_row(raw, default_confidence=default_confidence)
        if item:
            sources.append(item)
    return sources


def _extract_policy_decisions(diagnostics: dict[str, Any]) -> list[ReasoningPolicyDecision]:
    decisions: list[ReasoningPolicyDecision] = []
    self_check = dict(diagnostics.get("self_check") or {})
    decisions.append(
        build_reasoning_policy_decision(
            policy_name="self_check",
            status=self_check.get("status", ""),
            reason=";".join(str(x or "") for x in list(self_check.get("reasons") or [])),
        )
    )
    verify = dict(diagnostics.get("verify") or {})
    decisions.append(
        build_reasoning_policy_decision(
            policy_name="verify",
            status=verify.get("status", ""),
            reason=";".join(str(x or "") for x in list(verify.get("reasons") or [])),
        )
    )
    policy = dict(diagnostics.get("reasoning_execution_policy") or {})
    if policy:
        decisions.append(
            build_reasoning_policy_decision(
                policy_name="execution_policy",
                status="applied",
                reason=(
                    f"max_steps={int(policy.get('max_steps', 0) or 0)},"
                    f"max_retries={int(policy.get('max_retries', 0) or 0)},"
                    f"max_latency_ms={int(policy.get('max_latency_ms', 0) or 0)}"
                ),
            )
        )
    for raw in list(diagnostics.get("policy_decisions") or []):
        item = raw if isinstance(raw, dict) else {}
        decisions.append(
            build_reasoning_policy_decision(
                policy_name=item.get("policy_name", ""),
                status=item.get("status", ""),
                reason=item.get("reason", ""),
            )
        )
    return decisions


def _extract_risk_flags(*, diagnostics: dict[str, Any], warnings: list[str]) -> list[object]:
    flags: list[object] = list(warnings or [])
    self_check = dict(diagnostics.get("self_check") or {})
    verify = dict(diagnostics.get("verify") or {})
    self_check_status = str(self_check.get("status", "") or "").strip().lower()
    verify_status = str(verify.get("status", "") or "").strip().lower()
    if self_check_status == "warn":
        flags.append("self_check_warn")
    if verify_status == "warn":
        flags.append("verify_warn")
    if not bool(diagnostics.get("evidence_contract_valid_minimal", True)):
        flags.append("evidence_contract_minimal_invalid")
    return flags


def collect_reasoning_execution_receipt(
    *,
    trace_id: str,
    replay_token: str,
    query: str,
    answer: str,
    diagnostics: dict[str, Any],
    warnings: list[str] | None = None,
) -> ReasoningExecutionReceipt:
    """Collect normalized execution receipt from diagnostics boundaries."""
    normalized_diag = dict(diagnostics or {})
    reasoning_quality = dict(normalized_diag.get("reasoning_quality") or {})
    confidence = dict(reasoning_quality.get("confidence") or {})
    confidence_score = float(confidence.get("confidence_score", 0.0) or 0.0)
    return build_reasoning_execution_receipt(
        trace_id=trace_id,
        replay_token=replay_token,
        query=query,
        answer=answer,
        confidence_score=confidence_score,
        sources=_extract_sources(
            diagnostics=normalized_diag,
            default_confidence=confidence_score,
        ),
        policy_decisions=_extract_policy_decisions(normalized_diag),
        risk_flags=_extract_risk_flags(
            diagnostics=normalized_diag,
            warnings=list(warnings or []),
        ),
    )
