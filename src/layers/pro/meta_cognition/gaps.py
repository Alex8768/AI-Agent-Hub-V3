from __future__ import annotations

from typing import TypedDict


class KnowledgeGap(TypedDict):
    gap_id: str
    topic: str
    gap_type: str
    confidence: float
    evidence_refs: list[str]
    source: str
    message: str


class GapMap(TypedDict):
    session_id: str
    status: str
    total_gaps: int
    high_priority_gaps: int
    coverage_score: float
    gaps: list[KnowledgeGap]
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


def _normalize_gap_type(value: object) -> str:
    normalized = _normalize_string(value).lower()
    if normalized in {"missing_data", "contradiction", "low_confidence"}:
        return normalized
    return "missing_data"


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw)
        if item:
            rows.append(item)
    return sorted(set(rows))


def build_knowledge_gap(
    *,
    gap_id: object,
    topic: object,
    gap_type: object,
    confidence: object = 0.0,
    evidence_refs: object = None,
    source: object = "",
    message: object = "",
) -> KnowledgeGap:
    normalized_topic = _normalize_string(topic)
    normalized_type = _normalize_gap_type(gap_type)
    normalized_gap_id = _normalize_string(gap_id) or f"{normalized_type}:{normalized_topic.lower()}"
    return {
        "gap_id": normalized_gap_id,
        "topic": normalized_topic,
        "gap_type": normalized_type,
        "confidence": _normalize_confidence_01(confidence),
        "evidence_refs": _normalize_string_list(evidence_refs),
        "source": _normalize_string(source),
        "message": _normalize_string(message),
    }


def build_gap_map(
    *,
    session_id: object,
    gaps: object,
    high_priority_confidence: object = 0.7,
    warnings: object = None,
) -> GapMap:
    normalized: list[KnowledgeGap] = []
    for raw in list(gaps or []):
        row = dict(raw or {})
        normalized.append(
            build_knowledge_gap(
                gap_id=row.get("gap_id", ""),
                topic=row.get("topic", ""),
                gap_type=row.get("gap_type", "missing_data"),
                confidence=row.get("confidence", 0.0),
                evidence_refs=row.get("evidence_refs", []),
                source=row.get("source", ""),
                message=row.get("message", ""),
            )
        )
    normalized.sort(
        key=lambda x: (
            str(x.get("gap_type", "")),
            str(x.get("topic", "")),
            str(x.get("gap_id", "")),
        )
    )

    high_priority_threshold = _normalize_confidence_01(high_priority_confidence)
    total = len(normalized)
    high_priority = len([row for row in normalized if float(row.get("confidence", 0.0)) >= high_priority_threshold])
    coverage_score = 1.0
    if total > 0:
        coverage_score = max(0.0, min(1.0, 1.0 - (high_priority / float(total))))

    reason_codes: list[str] = []
    if total > 0:
        reason_codes.append("gaps_present")
    if high_priority > 0:
        reason_codes.append("high_priority_gaps_present")
    status = "clear"
    if high_priority > 0:
        status = "needs_attention"
    elif total > 0:
        status = "monitor"

    normalized_warnings = sorted(set([_normalize_string(x) for x in list(warnings or []) if _normalize_string(x)]))
    return {
        "session_id": _normalize_string(session_id),
        "status": status,
        "total_gaps": total,
        "high_priority_gaps": high_priority,
        "coverage_score": coverage_score,
        "gaps": normalized,
        "reason_codes": sorted(set(reason_codes)),
        "warnings": normalized_warnings,
    }
