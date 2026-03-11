from __future__ import annotations


def build_conversational_runtime_parity_bundle(
    *,
    diagnostics: dict[str, object],
    query: str,
    answer: str,
    normalize_language_tag_fn: object,
    answer_language_fn: object,
    is_unknown_style_answer_fn: object,
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    query_text = str(query or "")
    answer_text = str(answer or "")
    assistant_mode_enabled = bool(diag.get("assistant_mode_enabled", False))
    response_mode = str(diag.get("response_mode", "") or "")
    response_language = normalize_language_tag_fn(
        str(diag.get("response_language", "auto") or "auto"),
        query=query_text,
    )
    answer_language = answer_language_fn(answer_text)
    has_evidence = int(diag.get("retrieved_provenance_count", 0) or 0) > 0
    unknown_style = bool(is_unknown_style_answer_fn(answer_text))
    recovery_applied = bool(diag.get("assistant_chat_recovery_applied", False))
    friendliness_applied = "assistant_low_evidence_friendliness_applied" in {
        str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()
    }
    reason_codes: list[str] = ["conversational_runtime_parity_evaluated"]
    status = "pass"
    if assistant_mode_enabled:
        reason_codes.append("conversational_runtime_assistant_enabled")
    else:
        reason_codes.append("conversational_runtime_assistant_disabled")
    if answer_language == response_language:
        reason_codes.append("conversational_runtime_language_aligned")
    else:
        status = "warn"
        reason_codes.append("conversational_runtime_language_mismatch")
    if assistant_mode_enabled and not has_evidence and unknown_style:
        status = "warn"
        reason_codes.append("conversational_runtime_low_evidence_unknown_style")
    else:
        reason_codes.append("conversational_runtime_low_evidence_style_ok")
    if recovery_applied:
        reason_codes.append("conversational_runtime_recovery_applied")
    if friendliness_applied:
        reason_codes.append("conversational_runtime_friendliness_applied")
    return {
        "contract_version": "v1",
        "mode": "conversational_runtime_parity_guarded",
        "status": status,
        "inputs": {
            "assistant_mode_enabled": assistant_mode_enabled,
            "response_mode": response_mode,
            "response_language": response_language,
            "answer_language": answer_language,
            "has_evidence": has_evidence,
            "unknown_style_answer": unknown_style,
            "recovery_applied": recovery_applied,
            "friendliness_applied": friendliness_applied,
        },
        "thresholds": {
            "require_language_alignment": True,
            "require_non_unknown_style_when_low_evidence": True,
        },
        "reason_codes": sorted(set(reason_codes)),
    }
