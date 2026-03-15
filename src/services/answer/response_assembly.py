from __future__ import annotations

from typing import Any

from src.adapters.logging_adapter import get_logger

_LOGGER = get_logger()


async def run_answer_response_assembly(
    *,
    resp: object,
    req: object,
    llm: object | None,
    assistant_mode_enabled: bool,
    assistant_response_language: str,
    build_assistant_recovery_policy_contract: object,
    apply_assistant_recovery_policy_guards: object,
    build_assistant_chat_recovery_answer: object,
    normalize_low_evidence_friendliness: object,
    build_conversational_runtime_parity_bundle: object,
    build_truthfulness_guard_bundle: object,
    calibrate_confidence_with_truthfulness_guard: object,
) -> object:
    try:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        has_evidence = int(diag.get("retrieved_provenance_count", 0) or 0) > 0
        plan_intent = str((dict(diag.get("assistant_plan") or {})).get("intent", "general_query") or "general_query")
        recovery_policy = build_assistant_recovery_policy_contract()
        allow_recovery, recovery_policy_eval = apply_assistant_recovery_policy_guards(
            policy_contract=recovery_policy,
            assistant_mode_enabled=assistant_mode_enabled,
            has_evidence=has_evidence,
            plan_intent=plan_intent,
            query=str(getattr(req, "query", "") or ""),
            target_language=str(assistant_response_language or "auto"),
        )
        diag["assistant_recovery_policy"] = recovery_policy_eval
        policy_reasons = [str(x) for x in list(recovery_policy_eval.get("applied_reason_codes") or []) if str(x or "").strip()]
        if policy_reasons:
            reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
            reason_codes.extend(policy_reasons)
            diag["planning_reason_codes"] = sorted(set(reason_codes))
        if allow_recovery:
            recovered = await build_assistant_chat_recovery_answer(
                query=str(getattr(req, "query", "") or ""),
                language=str(assistant_response_language or "auto"),
                llm=llm,
                current_answer=str(getattr(resp, "answer", "") or ""),
            )
            if recovered and recovered.strip() != str(getattr(resp, "answer", "") or "").strip():
                resp.answer = recovered
                reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
                reason_codes.append("assistant_chat_recovery_applied")
                diag["planning_reason_codes"] = sorted(set(reason_codes))
                diag["assistant_chat_recovery_applied"] = True
        if assistant_mode_enabled and not has_evidence:
            normalized_low_evidence_answer = normalize_low_evidence_friendliness(
                query=str(getattr(req, "query", "") or ""),
                language=str(assistant_response_language or "auto"),
                answer=str(getattr(resp, "answer", "") or ""),
            )
            if normalized_low_evidence_answer.strip() != str(getattr(resp, "answer", "") or "").strip():
                resp.answer = normalized_low_evidence_answer
                reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
                reason_codes.append("assistant_low_evidence_friendliness_applied")
                diag["planning_reason_codes"] = sorted(set(reason_codes))
        conversational_runtime_parity = build_conversational_runtime_parity_bundle(
            diagnostics=diag,
            query=str(getattr(req, "query", "") or ""),
            answer=str(getattr(resp, "answer", "") or ""),
        )
        diag["conversational_runtime_parity"] = conversational_runtime_parity
        reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
        reason_codes.extend(list(conversational_runtime_parity.get("reason_codes") or []))
        truthfulness_guard = build_truthfulness_guard_bundle(
            query=str(getattr(req, "query", "") or ""),
            answer=str(getattr(resp, "answer", "") or ""),
            diagnostics=diag,
        )
        diag["truthfulness_guard"] = dict(truthfulness_guard or {})
        truthfulness_reasons = [
            str(x)
            for x in list((dict(truthfulness_guard or {})).get("reason_codes") or [])
            if str(x or "").strip() and str(x) != "truthfulness_guard_evaluated"
        ]
        calibrated_confidence, confidence_calibration = calibrate_confidence_with_truthfulness_guard(
            confidence=getattr(resp, "confidence", 0.0),
            truthfulness_guard_bundle=truthfulness_guard,
        )
        if float(calibrated_confidence) != float(getattr(resp, "confidence", 0.0) or 0.0):
            resp.confidence = float(calibrated_confidence)
        diag["truthfulness_guard"] = {
            **dict(diag.get("truthfulness_guard") or {}),
            **dict(confidence_calibration or {}),
        }
        guard_diag = dict(diag.get("truthfulness_guard") or {})
        guard_diag["logic_consistency"] = dict(guard_diag.get("logic_consistency") or {})
        guard_diag["evidence_alignment"] = dict(guard_diag.get("evidence_alignment") or {})
        guard_diag["claim_graph"] = dict(guard_diag.get("claim_graph") or {})
        guard_diag["evidence_bindings"] = [dict(x) for x in list(guard_diag.get("evidence_bindings") or [])]
        guard_diag["reasoning_process"] = [dict(x) for x in list(guard_diag.get("reasoning_process") or [])]
        guard_diag["trust_summary"] = str(guard_diag.get("trust_summary", "") or "")
        diag["truthfulness_guard"] = guard_diag
        truthfulness_reasons.extend(
            [
                str(x)
                for x in list((dict(confidence_calibration or {})).get("reason_codes") or [])
                if str(x or "").strip() and str(x) != "truthfulness_guard_confidence_calibrated"
            ]
        )
        reason_codes.extend(truthfulness_reasons)
        diag["planning_reason_codes"] = sorted(set(reason_codes))
        resp.diagnostics = diag
    except Exception as exc:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
        reason_codes.append("answer_response_assembly_soft_failure")
        diag["planning_reason_codes"] = sorted(set(reason_codes))
        resp.diagnostics = diag
        _LOGGER.warning(
            "Answer response assembly soft-failure handled",
            context={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_response_assembly_soft_failure",
            },
        )
    return resp
