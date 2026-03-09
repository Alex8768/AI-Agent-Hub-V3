from __future__ import annotations

from typing import TypedDict


class UncertaintySignal(TypedDict):
    code: str
    severity: str
    confidence: float
    source: str
    message: str


class UncertaintySummary(TypedDict):
    status: str
    uncertainty_score: float
    signals: list[UncertaintySignal]
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


def _severity_weight(severity: str) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.75
    if severity == "medium":
        return 0.5
    return 0.25


def build_uncertainty_signal(
    *,
    code: object,
    severity: object = "medium",
    confidence: object = 0.0,
    source: object = "",
    message: object = "",
) -> UncertaintySignal:
    return {
        "code": _normalize_string(code).lower(),
        "severity": _normalize_severity(severity),
        "confidence": _normalize_confidence_01(confidence),
        "source": _normalize_string(source),
        "message": _normalize_string(message),
    }


def build_uncertainty_summary(
    *,
    signals: object,
    low_confidence_threshold: object = 0.45,
    high_uncertainty_threshold: object = 0.65,
    warnings: object = None,
) -> UncertaintySummary:
    normalized_signals: list[UncertaintySignal] = []
    for raw in list(signals or []):
        row = dict(raw or {})
        normalized_signals.append(
            build_uncertainty_signal(
                code=row.get("code", ""),
                severity=row.get("severity", "medium"),
                confidence=row.get("confidence", 0.0),
                source=row.get("source", ""),
                message=row.get("message", ""),
            )
        )
    normalized_signals.sort(
        key=lambda x: (
            str(x.get("code", "")),
            str(x.get("severity", "")),
            str(x.get("source", "")),
            str(x.get("message", "")),
        )
    )

    low_confidence_threshold_f = _normalize_confidence_01(low_confidence_threshold)
    high_uncertainty_threshold_f = _normalize_confidence_01(high_uncertainty_threshold)

    weighted_uncertainties: list[float] = []
    reason_codes: list[str] = []
    for row in normalized_signals:
        confidence = float(row.get("confidence", 0.0))
        severity = str(row.get("severity", "medium"))
        uncertainty = (1.0 - confidence) * _severity_weight(severity)
        weighted_uncertainties.append(uncertainty)
        if confidence < low_confidence_threshold_f:
            reason_codes.append("low_confidence_signal")
        if severity in {"high", "critical"}:
            reason_codes.append("high_severity_signal")

    score = 0.0
    if weighted_uncertainties:
        score = sum(weighted_uncertainties) / float(len(weighted_uncertainties))
    score = max(0.0, min(1.0, score))
    if score >= high_uncertainty_threshold_f:
        status = "high"
        reason_codes.append("uncertainty_above_threshold")
    elif score > 0.0:
        status = "medium"
    else:
        status = "low"

    normalized_warnings = sorted(
        set([_normalize_string(x) for x in list(warnings or []) if _normalize_string(x)])
    )
    return {
        "status": status,
        "uncertainty_score": score,
        "signals": normalized_signals,
        "reason_codes": sorted(set(reason_codes)),
        "warnings": normalized_warnings,
    }


class UncertaintyTracker:
    """Deterministic collector for meta-cognition uncertainty signals."""

    def __init__(self) -> None:
        self._signals: list[UncertaintySignal] = []

    def record(self, *, signal: object) -> UncertaintySignal:
        row = dict(signal or {})
        normalized = build_uncertainty_signal(
            code=row.get("code", ""),
            severity=row.get("severity", "medium"),
            confidence=row.get("confidence", 0.0),
            source=row.get("source", ""),
            message=row.get("message", ""),
        )
        self._signals.append(normalized)
        self._signals.sort(
            key=lambda x: (
                str(x.get("code", "")),
                str(x.get("severity", "")),
                str(x.get("source", "")),
                str(x.get("message", "")),
            )
        )
        return dict(normalized)

    def snapshot(self) -> list[UncertaintySignal]:
        return [dict(x) for x in self._signals]

    def build_summary(
        self,
        *,
        low_confidence_threshold: object = 0.45,
        high_uncertainty_threshold: object = 0.65,
        warnings: object = None,
    ) -> UncertaintySummary:
        return build_uncertainty_summary(
            signals=self._signals,
            low_confidence_threshold=low_confidence_threshold,
            high_uncertainty_threshold=high_uncertainty_threshold,
            warnings=warnings,
        )

    def clear(self) -> None:
        self._signals = []
