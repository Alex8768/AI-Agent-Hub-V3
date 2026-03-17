from __future__ import annotations

from typing import Any


async def run_container_pipeline(
    *,
    req: object,
    http: object,
    workspace_id: str,
    settings: object,
    runtime_context: dict[str, object],
    engine: object,
    hybrid: object,
    get_reasoning_engine: object,
    get_memory_store: object,
    run_primary_pipeline: object,
    run_post_orchestration_flow: object,
    run_diagnostics_merge_flow: object,
    build_post_orchestration_deps: object,
    build_diagnostics_merge_deps: object,
) -> Any:
    pipeline = await run_primary_pipeline(
        http=http,
        req=req,
        workspace_id=workspace_id,
        settings=settings,
        runtime_context=runtime_context,
        engine=engine,
        hybrid=hybrid,
        get_reasoning_engine=get_reasoning_engine,
        get_memory_store=get_memory_store,
    )
    resp = await run_post_orchestration_flow(
        req=req,
        http=http,
        resp=pipeline.resp,
        workspace_id=workspace_id,
        assistant_mode_enabled=pipeline.assistant_mode_enabled,
        assistant_proactive_enabled=pipeline.assistant_proactive_enabled,
        assistant_actions_enabled=pipeline.assistant_actions_enabled,
        assistant_response_language=pipeline.assistant_response_language,
        loaded_durable_approval=pipeline.loaded_durable_approval,
        loaded_durable_idempotency=pipeline.loaded_durable_idempotency,
        get_memory_store=get_memory_store,
        deps=build_post_orchestration_deps(),
    )
    return await run_diagnostics_merge_flow(
        req=req,
        resp=resp,
        workspace_id=workspace_id,
        loaded_durable_approval=pipeline.loaded_durable_approval,
        loaded_durable_idempotency=pipeline.loaded_durable_idempotency,
        get_memory_store=get_memory_store,
        deps=build_diagnostics_merge_deps(),
    )

