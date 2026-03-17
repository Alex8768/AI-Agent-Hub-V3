from __future__ import annotations

from typing import Any

from src.adapters.logging_adapter import get_logger
from src.layers.pro.reasoning.response_style import (
    build_natural_safe_terminal_response,
    is_low_information_answer,
    is_reasoning_stub_answer,
    is_simple_greeting_query,
    is_substantive_query,
    is_template_like_answer,
    is_unknown_style_answer,
)
from src.services.answer.risk_tier import (
    build_l2_safe_terminal,
    build_risk_tier_reason,
    classify_risk_tier,
)

_LOGGER = get_logger()


def _append_quality_trace(diag: dict[str, Any], marker: str) -> None:
    trace = [str(x) for x in list(diag.get("quality_trace") or []) if str(x or "").strip()]
    trace.append(str(marker))
    diag["quality_trace"] = sorted(set(trace))


def _is_substantive_query(query: str) -> bool:
    return bool(is_substantive_query(query))


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
        query_text = str(getattr(req, "query", "") or "")
        risk_tier = classify_risk_tier(query_text)
        diag["risk_tier"] = risk_tier
        diag["risk_tier_reason"] = build_risk_tier_reason(query_text, risk_tier)
        has_evidence = int(diag.get("retrieved_provenance_count", 0) or 0) > 0
        plan_intent = str((dict(diag.get("assistant_plan") or {})).get("intent", "general_query") or "general_query")
        recovery_policy = build_assistant_recovery_policy_contract()
        allow_recovery, recovery_policy_eval = apply_assistant_recovery_policy_guards(
            policy_contract=recovery_policy,
            assistant_mode_enabled=assistant_mode_enabled,
            has_evidence=has_evidence,
            plan_intent=plan_intent,
            query=query_text,
            target_language=str(assistant_response_language or "auto"),
        )
        diag["assistant_recovery_policy"] = recovery_policy_eval
        policy_reasons = [str(x) for x in list(recovery_policy_eval.get("applied_reason_codes") or []) if str(x or "").strip()]
        if policy_reasons:
            reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
            reason_codes.extend(policy_reasons)
            diag["planning_reason_codes"] = sorted(set(reason_codes))
            if "assistant_chat_recovery_policy_forced_fallback" in policy_reasons:
                _append_quality_trace(diag, "quality_trace:recovery_policy_forced_fallback")
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
                _append_quality_trace(diag, "quality_trace:assistant_recovery_applied")
        current_answer = str(getattr(resp, "answer", "") or "")
        # Anti-template routing: if final candidate still looks canned for non-greeting L0/L1, regenerate naturally.
        if (
            risk_tier in {"L0", "L1"}
            and current_answer.strip()
            and is_template_like_answer(current_answer)
            and not is_simple_greeting_query(query_text)
        ):
            resp.answer = await build_natural_safe_terminal_response(
                query=query_text,
                language=str(assistant_response_language or "auto"),
                llm=llm,
                risk_tier=risk_tier,
                current_answer="",
            )
            reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
            reason_codes.append("assistant_template_answer_rewritten")
            diag["planning_reason_codes"] = sorted(set(reason_codes))
            _append_quality_trace(diag, "quality_trace:template_answer_rewritten")
            current_answer = str(getattr(resp, "answer", "") or "")

        # L2 contract first: empty/stub -> plan/preview + confirm-required (do not overwrite with generic)
        if risk_tier == "L2" and (
            not current_answer.strip() or is_reasoning_stub_answer(current_answer)
        ):
            resp.answer = await build_natural_safe_terminal_response(
                query=query_text,
                language=str(assistant_response_language or "auto"),
                llm=llm,
                risk_tier=risk_tier,
                current_answer=build_l2_safe_terminal(
                    query_text,
                    str(assistant_response_language or "auto"),
                ),
            )
            reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
            reason_codes.append("assistant_l2_terminal_contract_enforced")
            diag["planning_reason_codes"] = sorted(set(reason_codes))
            _append_quality_trace(diag, "quality_trace:tier_contract_l2_enforced")
        else:
            # Tier contract: L0/L1 — no stub, empty, or clarification-only terminal
            should_replace_terminal = is_reasoning_stub_answer(current_answer) or (
                risk_tier in {"L0", "L1"}
                and (
                    is_template_like_answer(current_answer) and _is_substantive_query(query_text)
                    or not current_answer.strip()
                    or is_unknown_style_answer(current_answer)
                    or is_low_information_answer(current_answer)
                )
            )
            if should_replace_terminal:
                resp.answer = await build_natural_safe_terminal_response(
                    query=query_text,
                    language=str(assistant_response_language or "auto"),
                    llm=llm,
                    risk_tier=risk_tier,
                    current_answer="",  # force fresh safe response so unknown_style/stub are not re-used
                )
                reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
                reason_codes.append("assistant_terminal_answer_replaced")
                diag["planning_reason_codes"] = sorted(set(reason_codes))
                if is_reasoning_stub_answer(current_answer):
                    _append_quality_trace(diag, "quality_trace:stub_terminal_replaced")
                elif is_unknown_style_answer(current_answer) or is_low_information_answer(current_answer) or not current_answer.strip():
                    _append_quality_trace(diag, "quality_trace:tier_contract_l0_l1_enforced")
                else:
                    _append_quality_trace(diag, "quality_trace:template_terminal_replaced")
        if assistant_mode_enabled and not has_evidence:
            if not _is_substantive_query(query_text):
                normalized_low_evidence_answer = normalize_low_evidence_friendliness(
                    query=query_text,
                    language=str(assistant_response_language or "auto"),
                    answer=str(getattr(resp, "answer", "") or ""),
                )
                if normalized_low_evidence_answer.strip() != str(getattr(resp, "answer", "") or "").strip():
                    resp.answer = normalized_low_evidence_answer
                    reason_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
                    reason_codes.append("assistant_low_evidence_friendliness_applied")
                    diag["planning_reason_codes"] = sorted(set(reason_codes))
                    _append_quality_trace(diag, "quality_trace:low_evidence_normalized")
            else:
                _append_quality_trace(diag, "quality_trace:substantive_query_preserved")
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
