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
_EVIDENCE_ALIGNMENT_MIN_OVERLAP = 0.2
_CLAIM_BINDING_MIN_OVERLAP = 0.15
_STOPWORDS: set[str] = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "will",
    "have",
    "been",
    "were",
    "would",
    "there",
    "about",
    "into",
    "under",
    "your",
    "you",
    "are",
    "как",
    "это",
    "что",
    "для",
    "под",
    "или",
    "при",
    "без",
    "над",
    "она",
    "они",
    "его",
    "еще",
}
_CONTRADICTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("always", "sometimes"),
    ("never", "sometimes"),
    ("cannot", "can"),
    ("impossible", "possible"),
    ("always", "not always"),
    ("never", "not never"),
    ("всегда", "иногда"),
    ("никогда", "иногда"),
    ("невозможно", "возможно"),
    ("не может", "может"),
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _contains_phrase(*, text: str, phrases: tuple[str, ...]) -> bool:
    if not text:
        return False
    return any(str(phrase).strip().lower() in text for phrase in phrases if str(phrase).strip())


def _detect_contradiction_signals(*, normalized_answer: str) -> list[str]:
    signals: list[str] = []
    for left, right in _CONTRADICTION_PAIRS:
        if left in normalized_answer and right in normalized_answer:
            signals.append(f"{left}|{right}")
    return sorted(set(signals))


def _extract_keyword_tokens(*, text: str) -> set[str]:
    tokens = set(re.findall(r"[a-zа-я0-9]{4,}", text))
    return {token for token in tokens if token not in _STOPWORDS}


def _extract_claim_fragments(*, normalized_answer: str) -> list[str]:
    fragments = [
        fragment.strip()
        for fragment in re.split(r"[.;!?]|, but |, however | но | однако ", normalized_answer)
        if fragment.strip()
    ]
    return fragments[:6]


def _build_claim_graph_bundle(
    *,
    normalized_answer: str,
    diagnostics: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]], list[str]]:
    evidence_summary_text = _normalize_text(str(diagnostics.get("evidence_summary", "") or ""))
    evidence_tokens = _extract_keyword_tokens(text=evidence_summary_text)
    claim_fragments = _extract_claim_fragments(normalized_answer=normalized_answer)
    claims: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []
    reason_codes: list[str] = []
    unsupported_high_certainty = 0

    for idx, fragment in enumerate(claim_fragments, start=1):
        claim_id = f"c{idx}"
        claim_tokens = _extract_keyword_tokens(text=fragment)
        overlap_tokens = sorted(claim_tokens & evidence_tokens)
        overlap_ratio = (
            float(len(overlap_tokens)) / float(len(claim_tokens))
            if claim_tokens
            else 1.0
        )
        high_certainty = _contains_phrase(text=fragment, phrases=_CERTAINTY_PHRASES)
        bound = bool(evidence_tokens) and overlap_ratio >= _CLAIM_BINDING_MIN_OVERLAP
        if high_certainty and not bound:
            unsupported_high_certainty += 1
        claims.append(
            {
                "id": claim_id,
                "text": fragment,
                "high_certainty": high_certainty,
            }
        )
        bindings.append(
            {
                "claim_id": claim_id,
                "bound": bound,
                "overlap_ratio": round(overlap_ratio, 3),
                "overlap_token_count": len(overlap_tokens),
            }
        )

    claim_graph = {
        "status": "warn" if unsupported_high_certainty > 0 else "ok",
        "claims": claims,
        "edges": [],
    }
    if unsupported_high_certainty > 0:
        reason_codes.append("truthfulness_guard_claim_graph_mismatch_detected")
    return claim_graph, bindings, reason_codes


def _build_evidence_alignment_bundle(
    *,
    answer_text: str,
    diagnostics: dict[str, object],
    strong_certainty_detected: bool,
) -> tuple[dict[str, object], list[str]]:
    evidence_summary_text = _normalize_text(str(diagnostics.get("evidence_summary", "") or ""))
    answer_tokens = _extract_keyword_tokens(text=answer_text)
    evidence_tokens = _extract_keyword_tokens(text=evidence_summary_text)
    overlap_tokens = sorted(answer_tokens & evidence_tokens)
    overlap_ratio = (
        float(len(overlap_tokens)) / float(len(answer_tokens))
        if answer_tokens
        else 1.0
    )
    status = "ok"
    reason_codes: list[str] = []
    if strong_certainty_detected and answer_tokens and evidence_tokens and overlap_ratio < _EVIDENCE_ALIGNMENT_MIN_OVERLAP:
        status = "warn"
        reason_codes.append("truthfulness_guard_evidence_claim_mismatch_detected")
    return {
        "status": status,
        "overlap_ratio": round(overlap_ratio, 3),
        "overlap_token_count": len(overlap_tokens),
        "claim_token_count": len(answer_tokens),
    }, reason_codes


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
    contradiction_signals = _detect_contradiction_signals(normalized_answer=normalized_answer)
    evidence_alignment, evidence_alignment_reason_codes = _build_evidence_alignment_bundle(
        answer_text=normalized_answer,
        diagnostics=diag,
        strong_certainty_detected=has_strong_certainty,
    )
    claim_graph, evidence_bindings, claim_graph_reason_codes = _build_claim_graph_bundle(
        normalized_answer=normalized_answer,
        diagnostics=diag,
    )

    if not has_evidence and has_strong_certainty:
        reason_codes.append("truthfulness_guard_low_evidence_high_certainty_claim")
    if has_source_deference:
        reason_codes.append("truthfulness_guard_source_deference_detected")
    if contradiction_signals:
        reason_codes.append("truthfulness_guard_internal_contradiction_detected")
    reason_codes.extend(evidence_alignment_reason_codes)
    reason_codes.extend(claim_graph_reason_codes)
    if not normalized_query and not normalized_answer:
        reason_codes.append("truthfulness_guard_empty_payload")

    unique_reason_codes = sorted(set(reason_codes))
    risk_reasons = [code for code in unique_reason_codes if code not in {"truthfulness_guard_evaluated"}]
    status = "warn" if risk_reasons else "ok"
    logic_status = "warn" if contradiction_signals else "ok"
    trust_summary = (
        "Trust reduced: internal contradiction patterns detected."
        if contradiction_signals
        else (
            "Trust reduced: unsupported high-certainty claims detected."
            if claim_graph.get("status") == "warn"
            else (
            "Trust reduced: claim-evidence mismatch detected."
            if evidence_alignment.get("status") == "warn"
            else "Trust checks passed: no contradiction or evidence mismatch signals."
            )
        )
    )
    reasoning_process = [
        {
            "step": "logic_consistency_check",
            "status": logic_status,
        },
        {
            "step": "evidence_claim_alignment_check",
            "status": str(evidence_alignment.get("status", "ok") or "ok"),
        },
        {
            "step": "claim_graph_binding_check",
            "status": str(claim_graph.get("status", "ok") or "ok"),
        },
    ]

    return {
        "contract_version": "v1",
        "mode": "deterministic_heuristic",
        "status": status,
        "reason_codes": unique_reason_codes,
        "trust_summary": trust_summary,
        "reasoning_process": reasoning_process,
        "logic_consistency": {
            "status": logic_status,
            "contradiction_signals": contradiction_signals,
        },
        "evidence_alignment": evidence_alignment,
        "claim_graph": claim_graph,
        "evidence_bindings": evidence_bindings,
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
