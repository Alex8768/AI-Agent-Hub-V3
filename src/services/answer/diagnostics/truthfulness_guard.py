"""Deterministic truthfulness/consistency guard seam for answer diagnostics."""

from __future__ import annotations

import re

_CERTAINTY_PHRASES: tuple[str, ...] = (
    "definitely",
    "certainly",
    "guaranteed",
    "absolutely",
    "без сомнений",
    "абсолютно точно",
    "гарантированно",
)

_SOURCE_DEFERENCE_PHRASES: tuple[str, ...] = (
    "according to wikipedia",
    "wikipedia says",
    "as wikipedia states",
    "согласно википедии",
    "википедия говорит",
    "как написано в википедии",
)
_WARN_CONFIDENCE_CAP = 0.55


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _contains_phrase(*, text: str, phrases: tuple[str, ...]) -> bool:
    if not text:
        return False
    return any(str(phrase).strip().lower() in text for phrase in phrases if str(phrase).strip())


def build_truthfulness_guard_bundle(
    *,
    query: str,
    answer: str,
    diagnostics: dict[str, object] | None = None,
) -> dict[str, object]:
    normalized_query = _normalize_text(query)
    normalized_answer = _normalize_text(answer)
    diag = dict(diagnostics or {})
    reason_codes: list[str] = ["truthfulness_guard_evaluated"]

    evidence_count = int(diag.get("retrieved_provenance_count", 0) or 0)
    has_evidence = evidence_count > 0
    has_strong_certainty = _contains_phrase(text=normalized_answer, phrases=_CERTAINTY_PHRASES)
    has_source_deference = _contains_phrase(text=normalized_answer, phrases=_SOURCE_DEFERENCE_PHRASES)

    if not has_evidence and has_strong_certainty:
        reason_codes.append("truthfulness_guard_low_evidence_high_certainty_claim")
    if has_source_deference:
        reason_codes.append("truthfulness_guard_source_deference_detected")
    if not normalized_query and not normalized_answer:
        reason_codes.append("truthfulness_guard_empty_payload")

    unique_reason_codes = sorted(set(reason_codes))
    risk_reasons = [code for code in unique_reason_codes if code not in {"truthfulness_guard_evaluated"}]
    status = "warn" if risk_reasons else "ok"

    return {
        "contract_version": "v1",
        "mode": "deterministic_heuristic",
        "status": status,
        "reason_codes": unique_reason_codes,
        "inputs": {
            "has_evidence": bool(has_evidence),
            "evidence_count": int(evidence_count),
            "strong_certainty_detected": bool(has_strong_certainty),
            "source_deference_detected": bool(has_source_deference),
        },
    }


def calibrate_confidence_with_truthfulness_guard(
    *,
    confidence: float | int | None,
    truthfulness_guard_bundle: dict[str, object] | None,
) -> tuple[float, dict[str, object]]:
    raw_confidence = float(confidence if confidence is not None else 0.0)
    normalized_before = max(0.0, min(1.0, raw_confidence))
    guard = dict(truthfulness_guard_bundle or {})
    guard_status = str(guard.get("status", "ok") or "ok").strip().lower()
    applied = guard_status == "warn" and normalized_before > _WARN_CONFIDENCE_CAP
    normalized_after = _WARN_CONFIDENCE_CAP if applied else normalized_before
    reason_codes = ["truthfulness_guard_confidence_calibrated"]
    if applied:
        reason_codes.append("truthfulness_guard_confidence_capped")
    return normalized_after, {
        "confidence_before": normalized_before,
        "confidence_after": normalized_after,
        "confidence_cap": _WARN_CONFIDENCE_CAP,
        "confidence_cap_applied": applied,
        "reason_codes": sorted(set(reason_codes)),
    }
