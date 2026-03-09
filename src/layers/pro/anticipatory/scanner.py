from __future__ import annotations

from typing import TypedDict


class OpportunitySignal(TypedDict):
    signal_id: str
    category: str
    confidence: float
    trigger: str
    rationale: str


class OpportunityScanResult(TypedDict):
    status: str
    opportunity_score: float
    signals: list[OpportunitySignal]
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


def _normalize_category(value: object) -> str:
    category = _normalize_string(value).lower()
    if category in {"follow_up", "automation", "summarization", "retrieval"}:
        return category
    return "follow_up"


def build_opportunity_signal(
    *,
    signal_id: object,
    category: object,
    confidence: object,
    trigger: object,
    rationale: object,
) -> OpportunitySignal:
    return {
        "signal_id": _normalize_string(signal_id),
        "category": _normalize_category(category),
        "confidence": _normalize_confidence_01(confidence),
        "trigger": _normalize_string(trigger),
        "rationale": _normalize_string(rationale),
    }


def build_opportunity_scan_result(
    *,
    signals: object,
    min_confidence: object = 0.6,
    warnings: object = None,
) -> OpportunityScanResult:
    normalized_signals: list[OpportunitySignal] = []
    for raw in list(signals or []):
        row = dict(raw or {})
        normalized_signals.append(
            build_opportunity_signal(
                signal_id=row.get("signal_id", ""),
                category=row.get("category", "follow_up"),
                confidence=row.get("confidence", 0.0),
                trigger=row.get("trigger", ""),
                rationale=row.get("rationale", ""),
            )
        )
    normalized_signals.sort(
        key=lambda x: (
            str(x.get("category", "")),
            str(x.get("signal_id", "")),
            str(x.get("trigger", "")),
        )
    )

    min_confidence_f = _normalize_confidence_01(min_confidence)
    selected = [x for x in normalized_signals if float(x.get("confidence", 0.0)) >= min_confidence_f]
    score = 0.0
    if selected:
        score = sum(float(x.get("confidence", 0.0)) for x in selected) / float(len(selected))
    status = "idle"
    reason_codes: list[str] = []
    if selected:
        status = "active"
        reason_codes.append("opportunities_detected")
    if normalized_signals and not selected:
        status = "monitor"
        reason_codes.append("below_threshold_opportunities")

    normalized_warnings = sorted(set([_normalize_string(x) for x in list(warnings or []) if _normalize_string(x)]))
    return {
        "status": status,
        "opportunity_score": max(0.0, min(1.0, score)),
        "signals": normalized_signals,
        "reason_codes": sorted(set(reason_codes)),
        "warnings": normalized_warnings,
    }


class OpportunityScanner:
    """Deterministic opportunity scanner for anticipatory safe mode."""

    def scan(
        self,
        *,
        context: object,
        session_memory: object = None,
        registry: object = None,
        min_confidence: object = 0.6,
    ) -> OpportunityScanResult:
        text = _normalize_string(context).lower()
        memory_text = _normalize_string(session_memory).lower()
        signals: list[OpportunitySignal] = []

        if any(token in text for token in ["document", "pdf", "report"]):
            signals.append(
                build_opportunity_signal(
                    signal_id="scan_summarization",
                    category="summarization",
                    confidence=0.75,
                    trigger="document_context",
                    rationale="Document-like context often benefits from summary follow-up",
                )
            )
        if any(token in text for token in ["next", "todo", "plan"]):
            signals.append(
                build_opportunity_signal(
                    signal_id="scan_follow_up",
                    category="follow_up",
                    confidence=0.7,
                    trigger="next_step_language",
                    rationale="User intent indicates potential follow-up action",
                )
            )
        if any(token in memory_text for token in ["unresolved", "pending", "blocked"]):
            signals.append(
                build_opportunity_signal(
                    signal_id="scan_memory_pending",
                    category="automation",
                    confidence=0.8,
                    trigger="session_memory_pending_state",
                    rationale="Session memory indicates unresolved workflow",
                )
            )
        if registry is not None:
            signals.append(
                build_opportunity_signal(
                    signal_id="scan_registry_available",
                    category="retrieval",
                    confidence=0.6,
                    trigger="registry_present",
                    rationale="Tool/agent registry is available for proactive options",
                )
            )
        return build_opportunity_scan_result(
            signals=signals,
            min_confidence=min_confidence,
            warnings=[],
        )
