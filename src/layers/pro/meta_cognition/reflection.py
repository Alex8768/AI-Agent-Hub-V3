from __future__ import annotations

from typing import TypedDict


class ReflectionInsight(TypedDict):
    code: str
    message: str
    severity: str


class ReflectionReport(TypedDict):
    status: str
    confidence_score: float
    uncertainty_score: float
    coverage_score: float
    insight_count: int
    insights: list[ReflectionInsight]
    reason_codes: list[str]
    warnings: list[str]


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_confidence_01(value: object) -> float:
    try:
        row = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, row))


def _normalize_severity(value: object) -> str:
    normalized = _normalize_string(value).lower()
    if normalized in {"low", "medium", "high", "critical"}:
        return normalized
    return "medium"


def build_reflection_insight(
    *,
    code: object,
    message: object,
    severity: object = "medium",
) -> ReflectionInsight:
    return {
        "code": _normalize_string(code).lower(),
        "message": _normalize_string(message),
        "severity": _normalize_severity(severity),
    }


def build_reflection_report(
    *,
    uncertainty_summary: object = None,
    gap_map: object = None,
    insights: object = None,
    warnings: object = None,
) -> ReflectionReport:
    uncertainty = dict(uncertainty_summary or {})
    gaps = dict(gap_map or {})

    uncertainty_score = _normalize_confidence_01(uncertainty.get("uncertainty_score", 0.0))
    coverage_score = _normalize_confidence_01(gaps.get("coverage_score", 1.0))
    confidence_score = max(0.0, min(1.0, (1.0 - uncertainty_score) * coverage_score))

    normalized_insights: list[ReflectionInsight] = []
    for raw in list(insights or []):
        row = dict(raw or {})
        normalized_insights.append(
            build_reflection_insight(
                code=row.get("code", ""),
                message=row.get("message", ""),
                severity=row.get("severity", "medium"),
            )
        )
    normalized_insights.sort(
        key=lambda x: (
            str(x.get("severity", "")),
            str(x.get("code", "")),
            str(x.get("message", "")),
        )
    )

    reason_codes = set([str(x) for x in list(uncertainty.get("reason_codes", []) or []) if str(x).strip()])
    reason_codes.update([str(x) for x in list(gaps.get("reason_codes", []) or []) if str(x).strip()])

    if confidence_score < 0.4:
        status = "rework"
        reason_codes.add("low_reflection_confidence")
    elif confidence_score < 0.7:
        status = "review"
    else:
        status = "ready"

    normalized_warnings = sorted(
        set(
            [
                _normalize_string(x)
                for x in (list(warnings or []) + list(uncertainty.get("warnings", []) or []) + list(gaps.get("warnings", []) or []))
                if _normalize_string(x)
            ]
        )
    )
    return {
        "status": status,
        "confidence_score": confidence_score,
        "uncertainty_score": uncertainty_score,
        "coverage_score": coverage_score,
        "insight_count": len(normalized_insights),
        "insights": normalized_insights,
        "reason_codes": sorted(reason_codes),
        "warnings": normalized_warnings,
    }
