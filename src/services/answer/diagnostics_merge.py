from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AnswerDiagnosticsMergeDeps:
    hydrate_durable_records_into_diagnostics: object
    persist_durable_records: object
    save_session_memory: object
    append_planning_reason_codes: object
    logger: object


async def run_answer_diagnostics_merge_flow(
    *,
    req: object,
    resp: object,
    workspace_id: str,
    loaded_durable_approval: dict[str, object],
    loaded_durable_idempotency: dict[str, object],
    get_memory_store: object,
    deps: AnswerDiagnosticsMergeDeps,
) -> object:
    try:
        resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
        deps.hydrate_durable_records_into_diagnostics(
            diagnostics=resp.diagnostics,
            loaded_approval=loaded_durable_approval,
            loaded_idempotency=loaded_durable_idempotency,
        )
    except Exception as exc:
        resp.diagnostics = deps.append_planning_reason_codes(
            diagnostics=dict(getattr(resp, "diagnostics", None) or {}),
            reason_codes=["answer_service_durable_hydration_soft_failure"],
        )
        deps.logger.warning(
            "Answer service soft-failure: durable diagnostics hydration skipped",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_service_durable_hydration_soft_failure",
            },
        )

    try:
        await deps.persist_durable_records(
            req=req,
            resp=resp,
            workspace_id=workspace_id,
            get_memory_store=get_memory_store,
        )
    except Exception as exc:
        resp.diagnostics = deps.append_planning_reason_codes(
            diagnostics=dict(getattr(resp, "diagnostics", None) or {}),
            reason_codes=["answer_service_durable_persist_soft_failure"],
        )
        deps.logger.warning(
            "Answer service soft-failure: durable records persist skipped",
            context={
                "workspace_id": str(workspace_id or ""),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "reason_code": "answer_service_durable_persist_soft_failure",
            },
        )

    await deps.save_session_memory(
        req=req,
        resp=resp,
        workspace_id=workspace_id,
        get_memory_store=get_memory_store,
    )
    return resp
