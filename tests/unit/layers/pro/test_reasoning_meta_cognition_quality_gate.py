from __future__ import annotations

from src.layers.pro.meta_cognition.gaps import build_gap_map
from src.layers.pro.meta_cognition.reflection import build_reflection_report
from src.layers.pro.meta_cognition.uncertainty import build_uncertainty_summary
from src.layers.pro.reasoning.engine import ReasoningEngine


def _build_runtime_diag() -> dict[str, object]:
    diagnostics = {
        "session_id": "s-1",
        "reasoning_quality": {
            "confidence": {
                "confidence_score": 0.35,
                "missing_claims": 2,
                "unsupported_claims": 1,
            },
            "coverage": {
                "coverage_score": 0.4,
            },
        },
        "verify": {"status": "warn", "reasons": ["verify_reason"]},
        "self_check": {"status": "warn", "reasons": ["self_check_reason"]},
    }
    return ReasoningEngine._build_meta_cognition_diagnostics(
        diagnostics=diagnostics,
        warnings=["w1"],
    )


def test_meta_cognition_quality_gate_contracts_are_deterministic() -> None:
    uncertainty_a = build_uncertainty_summary(
        signals=[{"code": "x", "severity": "high", "confidence": 0.2, "source": "quality"}],
        warnings=["w"],
    )
    uncertainty_b = build_uncertainty_summary(
        signals=[{"code": "x", "severity": "high", "confidence": 0.2, "source": "quality"}],
        warnings=["w"],
    )
    assert uncertainty_a == uncertainty_b

    gap_a = build_gap_map(
        session_id="s",
        gaps=[{"gap_id": "g1", "topic": "coverage", "gap_type": "missing_data", "confidence": 0.8}],
        warnings=["w"],
    )
    gap_b = build_gap_map(
        session_id="s",
        gaps=[{"gap_id": "g1", "topic": "coverage", "gap_type": "missing_data", "confidence": 0.8}],
        warnings=["w"],
    )
    assert gap_a == gap_b

    reflection_a = build_reflection_report(
        uncertainty_summary=uncertainty_a,
        gap_map=gap_a,
        insights=[{"code": "i1", "message": "msg", "severity": "high"}],
        warnings=["w"],
    )
    reflection_b = build_reflection_report(
        uncertainty_summary=uncertainty_b,
        gap_map=gap_b,
        insights=[{"code": "i1", "message": "msg", "severity": "high"}],
        warnings=["w"],
    )
    assert reflection_a == reflection_b


def test_meta_cognition_quality_gate_runtime_contract_shape_is_stable() -> None:
    runtime = _build_runtime_diag()
    assert set(runtime.keys()) == {"uncertainty", "gap_map", "reflection"}
    assert set(dict(runtime["uncertainty"]).keys()) == {
        "status",
        "uncertainty_score",
        "signals",
        "reason_codes",
        "warnings",
    }
    assert set(dict(runtime["gap_map"]).keys()) == {
        "session_id",
        "status",
        "total_gaps",
        "high_priority_gaps",
        "coverage_score",
        "gaps",
        "reason_codes",
        "warnings",
    }
    assert set(dict(runtime["reflection"]).keys()) == {
        "status",
        "confidence_score",
        "uncertainty_score",
        "coverage_score",
        "insight_count",
        "insights",
        "reason_codes",
        "warnings",
    }


def test_meta_cognition_quality_gate_runtime_reflection_parity() -> None:
    runtime = _build_runtime_diag()
    uncertainty = dict(runtime.get("uncertainty") or {})
    gap_map = dict(runtime.get("gap_map") or {})
    insights: list[dict[str, object]] = []
    if str(uncertainty.get("status", "")) == "high":
        insights.append(
            {
                "code": "reflection_uncertainty_high",
                "message": "High uncertainty requires additional verification",
                "severity": "high",
            }
        )
    if str(gap_map.get("status", "")) == "needs_attention":
        insights.append(
            {
                "code": "reflection_gap_attention",
                "message": "High-priority knowledge gaps require remediation",
                "severity": "high",
            }
        )
    reflection_direct = build_reflection_report(
        uncertainty_summary=uncertainty,
        gap_map=gap_map,
        insights=insights,
        warnings=["w1"],
    )
    assert dict(runtime.get("reflection") or {}) == reflection_direct
