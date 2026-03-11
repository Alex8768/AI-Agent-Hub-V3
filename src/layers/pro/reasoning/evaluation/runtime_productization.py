"""Advanced runtime diagnostics extracted from reasoning engine."""

from __future__ import annotations

from src.layers.pro.meta_cognition.gaps import build_gap_map
from src.layers.pro.meta_cognition.reflection import build_reflection_report
from src.layers.pro.meta_cognition.uncertainty import build_uncertainty_summary
from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)
from src.layers.pro.reasoning.enterprise.rollout_decision_model import (
    decide_enterprise_rollout_action,
)
from src.layers.pro.reasoning.optimization.optimization_decision_model import (
    decide_reasoning_optimization_action,
)
from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    build_reasoning_optimization_proposals,
)
from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    build_reasoning_optimization_signal_from_diagnostics,
)


def build_reasoning_optimization_diagnostics(
    *,
    diagnostics: dict[str, object],
    warnings: list[str],
) -> dict[str, object]:
    signal = build_reasoning_optimization_signal_from_diagnostics(
        diagnostics=dict(diagnostics or {}),
        warnings=list(warnings or []),
    )
    proposals_raw: list[dict[str, object]] = []
    confidence_score = float(signal.get("confidence_score", 0.0) or 0.0)
    coverage_score = float(signal.get("coverage_score", 0.0) or 0.0)
    pass_rate = float(signal.get("pass_rate", 0.0) or 0.0)
    retry_rate = float(signal.get("retry_rate", 0.0) or 0.0)
    signal_tags = [str(x) for x in list(signal.get("signal_tags") or [])]
    if confidence_score < 0.8:
        proposals_raw.append(
            {
                "proposal_id": "opt_confidence_guardrail",
                "parameter": "confidence_target",
                "current_value": confidence_score,
                "proposed_value": min(1.0, confidence_score + 0.2),
                "expected_gain": min(1.0, 0.8 - confidence_score),
                "risk_level": "medium",
                "rationale": ["low_confidence", *signal_tags],
            }
        )
    if coverage_score < 0.8:
        proposals_raw.append(
            {
                "proposal_id": "opt_coverage_guardrail",
                "parameter": "coverage_target",
                "current_value": coverage_score,
                "proposed_value": min(1.0, coverage_score + 0.2),
                "expected_gain": min(1.0, 0.8 - coverage_score),
                "risk_level": "low",
                "rationale": ["low_coverage", *signal_tags],
            }
        )
    if pass_rate < 0.9:
        proposals_raw.append(
            {
                "proposal_id": "opt_passrate_guardrail",
                "parameter": "verification_strictness",
                "current_value": pass_rate,
                "proposed_value": min(1.0, pass_rate + 0.1),
                "expected_gain": min(1.0, 0.9 - pass_rate),
                "risk_level": "medium",
                "rationale": ["low_pass_rate", *signal_tags],
            }
        )
    if retry_rate > 0.0:
        proposals_raw.append(
            {
                "proposal_id": "opt_retry_pressure",
                "parameter": "retry_budget",
                "current_value": retry_rate,
                "proposed_value": max(0.0, retry_rate - 0.5),
                "expected_gain": min(1.0, retry_rate * 0.5),
                "risk_level": "high",
                "rationale": ["retry_pressure", *signal_tags],
            }
        )
    proposals = build_reasoning_optimization_proposals(proposals=proposals_raw)
    decision = decide_reasoning_optimization_action(
        signal=signal,
        proposals=proposals,
        decision_id=f"optimization_decision:{str(signal.get('trace_id', '') or 'runtime')}",
    )
    return {
        "signal": dict(signal),
        "proposals": [dict(x) for x in list(proposals or [])],
        "decision": dict(decision),
    }


def build_enterprise_productization_diagnostics(
    *,
    diagnostics: dict[str, object],
    warnings: list[str],
) -> dict[str, object]:
    verify = dict(diagnostics.get("verify") or {})
    self_check = dict(diagnostics.get("self_check") or {})
    benchmark = diagnostics.get("reasoning_benchmark")
    optimization = diagnostics.get("reasoning_optimization")
    release_checks = {
        "verify": str(verify.get("status", "missing") or "missing"),
        "self_check": str(self_check.get("status", "missing") or "missing"),
        "reasoning_benchmark": "pass" if isinstance(benchmark, dict) else "missing",
        "reasoning_optimization": "pass" if isinstance(optimization, dict) else "missing",
    }
    policy = build_enterprise_release_gate_policy(
        profile_name="enterprise_default",
        required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
        blocking_checks=["verify", "self_check"],
        minimum_pass_rate=0.8,
        minimum_average_score=0.7,
        allow_skipped=False,
        require_benchmark_summary=True,
        require_optimization_review=True,
        allowed_warning_codes=[],
    )
    readiness = build_enterprise_readiness_contract_from_diagnostics(
        diagnostics={**dict(diagnostics or {}), "release_checks": release_checks},
        policy=policy,
        warnings=list(warnings or []),
    )
    rollout = decide_enterprise_rollout_action(
        readiness=readiness,
        policy=policy,
        decision_id=f"enterprise_rollout:{str(diagnostics.get('trace_id', '') or 'runtime')}",
        target_environment="production",
    )
    return {
        "release_gate_policy": dict(policy),
        "release_checks": dict(release_checks),
        "readiness": dict(readiness),
        "rollout_decision": dict(rollout),
    }


def build_meta_cognition_diagnostics(
    *,
    diagnostics: dict[str, object],
    warnings: list[str],
) -> dict[str, object]:
    reasoning_quality = dict(diagnostics.get("reasoning_quality") or {})
    confidence = dict(reasoning_quality.get("confidence") or {})
    coverage = dict(reasoning_quality.get("coverage") or {})
    verify = dict(diagnostics.get("verify") or {})
    self_check = dict(diagnostics.get("self_check") or {})

    confidence_score = float(confidence.get("confidence_score", 0.0) or 0.0)
    coverage_score = float(coverage.get("coverage_score", 0.0) or 0.0)
    missing_claims = int(confidence.get("missing_claims", 0) or 0)
    unsupported_claims = int(confidence.get("unsupported_claims", 0) or 0)

    uncertainty_signals: list[dict[str, object]] = []
    if confidence_score < 0.6:
        uncertainty_signals.append(
            {
                "code": "low_confidence",
                "severity": "high" if confidence_score < 0.4 else "medium",
                "confidence": confidence_score,
                "source": "reasoning_quality",
                "message": "Reasoning confidence below target",
            }
        )
    if str(verify.get("status", "") or "") == "warn":
        uncertainty_signals.append(
            {
                "code": "verify_warn",
                "severity": "medium",
                "confidence": max(0.0, 1.0 - float(len(verify.get("reasons") or [])) * 0.25),
                "source": "verify",
                "message": "Verify preflight produced warning status",
            }
        )
    if str(self_check.get("status", "") or "") == "warn":
        uncertainty_signals.append(
            {
                "code": "self_check_warn",
                "severity": "medium",
                "confidence": max(0.0, 1.0 - float(len(self_check.get("reasons") or [])) * 0.25),
                "source": "self_check",
                "message": "Self-check reported warning status",
            }
        )
    uncertainty = build_uncertainty_summary(
        signals=uncertainty_signals,
        warnings=list(warnings or []),
    )

    gaps_raw: list[dict[str, object]] = []
    if missing_claims > 0:
        gaps_raw.append(
            {
                "gap_id": "gap:missing_claims",
                "topic": "evidence coverage",
                "gap_type": "missing_data",
                "confidence": min(1.0, 0.5 + (missing_claims * 0.1)),
                "evidence_refs": [],
                "source": "reasoning_quality",
                "message": "Missing evidence-backed claims detected",
            }
        )
    if unsupported_claims > 0:
        gaps_raw.append(
            {
                "gap_id": "gap:unsupported_claims",
                "topic": "claim support",
                "gap_type": "low_confidence",
                "confidence": min(1.0, 0.5 + (unsupported_claims * 0.1)),
                "evidence_refs": [],
                "source": "reasoning_quality",
                "message": "Unsupported claims detected",
            }
        )
    if coverage_score < 0.6:
        gaps_raw.append(
            {
                "gap_id": "gap:coverage",
                "topic": "retrieval coverage",
                "gap_type": "missing_data",
                "confidence": max(0.0, 1.0 - coverage_score),
                "evidence_refs": [],
                "source": "reasoning_quality",
                "message": "Coverage score below target",
            }
        )
    gap_map = build_gap_map(
        session_id=str(diagnostics.get("session_id", "") or ""),
        gaps=gaps_raw,
        warnings=list(warnings or []),
    )

    insights: list[dict[str, object]] = []
    if str(uncertainty.get("status", "") or "") == "high":
        insights.append(
            {
                "code": "reflection_uncertainty_high",
                "message": "High uncertainty requires additional verification",
                "severity": "high",
            }
        )
    if str(gap_map.get("status", "") or "") == "needs_attention":
        insights.append(
            {
                "code": "reflection_gap_attention",
                "message": "High-priority knowledge gaps require remediation",
                "severity": "high",
            }
        )
    reflection = build_reflection_report(
        uncertainty_summary=uncertainty,
        gap_map=gap_map,
        insights=insights,
        warnings=list(warnings or []),
    )
    return {
        "uncertainty": dict(uncertainty),
        "gap_map": dict(gap_map),
        "reflection": dict(reflection),
    }
