from __future__ import annotations

from src.layers.pro.reasoning.response_style import (
    build_safe_terminal_response,
    is_low_information_answer,
    is_reasoning_stub_answer,
    is_template_like_answer,
    is_unknown_style_answer,
)
from src.services.answer.classifier import QueryType
from src.services.answer.response.language import detect_response_language


def _should_retry(answer: str) -> tuple[bool, list[str]]:
    reason_codes: list[str] = []
    if is_reasoning_stub_answer(answer):
        reason_codes.append("reflection_lite_stub_detected")
    if is_unknown_style_answer(answer):
        reason_codes.append("reflection_lite_unknown_style_detected")
    if is_low_information_answer(answer):
        reason_codes.append("reflection_lite_low_information_detected")
    if is_template_like_answer(answer):
        reason_codes.append("reflection_lite_template_detected")
    return bool(reason_codes), sorted(set(reason_codes))


def apply_reflection_lite(
    *,
    resp: object,
    req: object,
    query_type: QueryType | str,
    max_retries: int = 1,
) -> object:
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    answer = str(getattr(resp, "answer", "") or "")
    query = str(getattr(req, "query", "") or "")
    should_retry, detection_codes = _should_retry(answer)
    retries_used = 0
    rewrite_applied = False

    if should_retry and int(max_retries) > 0:
        language = str(diagnostics.get("response_language") or detect_response_language(query))
        regenerated = build_safe_terminal_response(
            query=query,
            language=language,
            current_answer="",
        ).strip()
        if regenerated:
            resp.answer = regenerated
            retries_used = 1
            rewrite_applied = True

    reason_codes = list(detection_codes)
    if rewrite_applied:
        reason_codes.append("reflection_lite_retry_applied")
    else:
        reason_codes.append("reflection_lite_retry_skipped")

    payload = {
        "contract_version": "v1",
        "mode": "post_answer_reflection",
        "query_type": str(query_type.value if isinstance(query_type, QueryType) else str(query_type or "dialog")),
        "max_retries": int(max_retries),
        "retries_used": int(retries_used),
        "rewrite_applied": bool(rewrite_applied),
        "reason_codes": sorted(set(reason_codes)),
    }
    diagnostics.setdefault("reflection_lite", payload)
    planning_codes = list(diagnostics.get("planning_reason_codes") or [])
    if rewrite_applied:
        planning_codes.append("assistant_reflection_lite_retry_applied")
    diagnostics["planning_reason_codes"] = sorted(set([str(x) for x in planning_codes if str(x)]))
    setattr(resp, "diagnostics", diagnostics)
    return resp

