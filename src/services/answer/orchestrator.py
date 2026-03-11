from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from fastapi import HTTPException, Request

from src.adapters.logging_adapter import get_logger
from src.observability.request_context import get_request_id

_LOGGER = get_logger()


def _append_planning_reason_codes(*, resp: object, reason_codes: list[str]) -> None:
    diag = dict(getattr(resp, "diagnostics", None) or {})
    merged_codes = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
    merged_codes.extend(str(x) for x in list(reason_codes or []) if str(x or "").strip())
    diag["planning_reason_codes"] = sorted(set(merged_codes))
    resp.diagnostics = diag


@dataclass(slots=True)
class AnswerOrchestrationResult:
    resp: object
    llm: object | None
    assistant_mode_enabled: bool
    assistant_proactive_enabled: bool
    assistant_actions_enabled: bool
    assistant_response_language: str
    loaded_durable_approval: dict[str, object]
    loaded_durable_idempotency: dict[str, object]
    get_memory_store: object


async def run_answer_orchestration_core(
    *,
    http: Request,
    req: object,
    workspace_id: str,
    settings: object,
    engine: object,
    hybrid: object,
    runtime_context: dict[str, object],
    get_reasoning_engine: object,
    get_memory_store: object,
    build_llm_adapter: object,
    load_session_memory: object,
    load_durable_records: object,
    retriever_adapter_cls: object,
    build_reasoning_runtime_adapter: object,
    detect_response_language: object,
    build_assistant_fallback_answer: object,
    apply_diagnostics: object,
) -> AnswerOrchestrationResult:
    soft_failure_reason_codes: list[str] = []
    llm, llm_enabled, llm_provider_name, llm_model, llm_error = await build_llm_adapter(settings=settings)
    assistant_mode_enabled = bool(runtime_context.get("assistant_mode_enabled", False))
    assistant_proactive_enabled = bool(runtime_context.get("assistant_proactive_enabled", False))
    assistant_actions_enabled = bool(runtime_context.get("assistant_actions_enabled", False))
    assistant_response_language = str(runtime_context.get("assistant_response_language", "auto") or "auto")
    session_memory_loaded, session_memory_hit = await load_session_memory(
        req=req,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )
    loaded_durable_approval, loaded_durable_idempotency = await load_durable_records(
        req=req,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )

    retriever = retriever_adapter_cls(engine=engine, hybrid=hybrid, workspace_id=workspace_id)
    reasoning = build_reasoning_runtime_adapter(
        reasoning_factory=get_reasoning_engine,
        retriever=retriever,
        llm=llm,
    )
    if reasoning is None:
        raise HTTPException(status_code=404, detail="Not Found")

    t0 = perf_counter()
    resp = await reasoning.synthesize(req)
    total_ms = (perf_counter() - t0) * 1000.0
    if assistant_mode_enabled and not list(getattr(resp, "provenance", []) or []):
        assistant_response_language = detect_response_language(str(getattr(req, "query", "") or ""))
        resp.answer = build_assistant_fallback_answer(
            query=str(getattr(req, "query", "") or ""),
            language=assistant_response_language,
        )

    try:
        resp.request_id = get_request_id(http) or ""
    except Exception as exc:
        try:
            object.__setattr__(resp, "request_id", "")
        except Exception:
            pass
        soft_failure_reason_codes.append("answer_orchestrator_request_id_assignment_failed")
        _LOGGER.warning(
            "Answer orchestrator soft-failure: request_id assignment failed",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_orchestrator_request_id_assignment_failed",
            },
        )
    try:
        resp.workspace_id = workspace_id or ""
    except Exception as exc:
        try:
            object.__setattr__(resp, "workspace_id", "")
        except Exception:
            pass
        soft_failure_reason_codes.append("answer_orchestrator_workspace_id_assignment_failed")
        _LOGGER.warning(
            "Answer orchestrator soft-failure: workspace_id assignment failed",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_orchestrator_workspace_id_assignment_failed",
            },
        )
    try:
        resp.timings = dict(resp.timings or {})
        resp.timings.setdefault("total_ms", float(total_ms))
    except Exception as exc:
        soft_failure_reason_codes.append("answer_orchestrator_timing_assignment_failed")
        _LOGGER.warning(
            "Answer orchestrator soft-failure: timings assignment failed",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_orchestrator_timing_assignment_failed",
            },
        )

    await apply_diagnostics(
        resp=resp,
        req=req,
        http=http,
        workspace_id=workspace_id,
        retriever=retriever,
        llm=llm,
        llm_enabled=llm_enabled,
        llm_provider_name=llm_provider_name,
        llm_model=llm_model,
        llm_error=llm_error,
        assistant_mode_enabled=assistant_mode_enabled,
        assistant_proactive_enabled=assistant_proactive_enabled,
        assistant_actions_enabled=assistant_actions_enabled,
        assistant_response_language=assistant_response_language,
        session_memory_loaded=session_memory_loaded,
        session_memory_hit=session_memory_hit,
        durable_approval_record_loaded=bool(loaded_durable_approval),
        durable_idempotency_record_loaded=bool(loaded_durable_idempotency),
    )
    if soft_failure_reason_codes:
        _append_planning_reason_codes(resp=resp, reason_codes=soft_failure_reason_codes)

    return AnswerOrchestrationResult(
        resp=resp,
        llm=llm,
        assistant_mode_enabled=assistant_mode_enabled,
        assistant_proactive_enabled=assistant_proactive_enabled,
        assistant_actions_enabled=assistant_actions_enabled,
        assistant_response_language=assistant_response_language,
        loaded_durable_approval=dict(loaded_durable_approval or {}),
        loaded_durable_idempotency=dict(loaded_durable_idempotency or {}),
        get_memory_store=get_memory_store,
    )
