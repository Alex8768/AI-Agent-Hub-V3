from __future__ import annotations

from typing import TypedDict


class ProactiveSuggestion(TypedDict):
    suggestion_id: str
    suggestion_type: str
    confidence: float
    rationale: str
    action_hint: str
    source_signal_id: str


class ProactiveSuggestionBundle(TypedDict):
    status: str
    suggestions: list[ProactiveSuggestion]
    top_suggestion_id: str
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


def _normalize_suggestion_type(value: object) -> str:
    normalized = _normalize_string(value).lower()
    if normalized in {"follow_up", "automation", "summarization", "retrieval"}:
        return normalized
    return "follow_up"


def build_proactive_suggestion(
    *,
    suggestion_id: object,
    suggestion_type: object,
    confidence: object,
    rationale: object,
    action_hint: object,
    source_signal_id: object = "",
) -> ProactiveSuggestion:
    return {
        "suggestion_id": _normalize_string(suggestion_id),
        "suggestion_type": _normalize_suggestion_type(suggestion_type),
        "confidence": _normalize_confidence_01(confidence),
        "rationale": _normalize_string(rationale),
        "action_hint": _normalize_string(action_hint),
        "source_signal_id": _normalize_string(source_signal_id),
    }


def rank_proactive_suggestions(
    *,
    suggestions: object,
    limit: object = 3,
) -> list[ProactiveSuggestion]:
    normalized: list[ProactiveSuggestion] = []
    for raw in list(suggestions or []):
        row = dict(raw or {})
        normalized.append(
            build_proactive_suggestion(
                suggestion_id=row.get("suggestion_id", ""),
                suggestion_type=row.get("suggestion_type", "follow_up"),
                confidence=row.get("confidence", 0.0),
                rationale=row.get("rationale", ""),
                action_hint=row.get("action_hint", ""),
                source_signal_id=row.get("source_signal_id", ""),
            )
        )
    normalized.sort(
        key=lambda x: (
            -float(x.get("confidence", 0.0)),
            str(x.get("suggestion_type", "")),
            str(x.get("suggestion_id", "")),
        )
    )
    lim = max(0, int(limit or 0))
    if lim <= 0:
        return normalized
    return normalized[:lim]


def build_proactive_suggestion_bundle(
    *,
    suggestions: object,
    limit: object = 3,
    warnings: object = None,
) -> ProactiveSuggestionBundle:
    ranked = rank_proactive_suggestions(suggestions=suggestions, limit=limit)
    status = "idle"
    reason_codes: list[str] = []
    if ranked:
        status = "active"
        reason_codes.append("suggestions_available")
    top_id = str((ranked[0] or {}).get("suggestion_id", "") or "") if ranked else ""
    normalized_warnings = sorted(set([_normalize_string(x) for x in list(warnings or []) if _normalize_string(x)]))
    return {
        "status": status,
        "suggestions": ranked,
        "top_suggestion_id": top_id,
        "reason_codes": sorted(set(reason_codes)),
        "warnings": normalized_warnings,
    }
