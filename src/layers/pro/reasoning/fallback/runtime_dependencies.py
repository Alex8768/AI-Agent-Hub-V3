from __future__ import annotations

from src.core.config import get_settings
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    AnswerResponse,
)
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.control.loop_guard import (
    build_bounded_plan_steps_with_loop_guard as _build_bounded_plan_steps_with_loop_guard,
)
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps
from src.layers.pro.reasoning.evaluation.runtime_diagnostics import (
    apply_fallback_response_diagnostics as _apply_fallback_response_diagnostics,
    build_fallback_planner_observations as _build_fallback_planner_observations,
)
from src.layers.pro.reasoning.evaluation.runtime_productization import (
    build_fallback_answer_response as _build_fallback_answer_response,
    synthesize_fallback_with_full_runtime_dependencies as _synthesize_fallback_with_full_runtime_dependencies,
)
from src.layers.pro.reasoning.kernel import build_reasoning_planner_runtime
from src.layers.pro.reasoning.multi_agent.runtime_contracts import (
    build_multi_agent_coordination_plan_for_runtime as _build_multi_agent_coordination_plan_for_runtime,
    enrich_step_results_with_multi_agent_contract as _enrich_step_results_with_multi_agent_contract,
)
from src.layers.pro.reasoning.tool_safety.runtime_guard import apply_tool_safety_runtime_guard
from src.layers.pro.reasoning.diagnostics.runtime_contracts import (
    apply_reasoning_runtime_warning_flags as _apply_reasoning_runtime_warning_flags,
)

_PLANNER_RUNTIME = build_reasoning_planner_runtime()
create_reasoning_plan = _PLANNER_RUNTIME["create_plan"]
execute_plan_steps = _PLANNER_RUNTIME["execute_steps"]
build_reasoning_prompt = _PLANNER_RUNTIME["build_prompt"]


async def synthesize_fallback_with_engine_runtime_dependencies(
    *,
    engine: object,
    request: object,
    error: str | None = None,
    create_reasoning_plan_fn: object | None = None,
    build_reasoning_execution_policy_fn: object | None = None,
    execute_plan_steps_fn: object | None = None,
) -> object:
    create_reasoning_plan_impl = create_reasoning_plan_fn or create_reasoning_plan
    build_reasoning_execution_policy_impl = (
        build_reasoning_execution_policy_fn or build_reasoning_execution_policy
    )
    execute_plan_steps_impl = execute_plan_steps_fn or execute_plan_steps
    return await _synthesize_fallback_with_full_runtime_dependencies(
        request=request,
        retriever=getattr(engine, "retriever"),
        error=error,
        get_settings_fn=get_settings,
        llm=getattr(engine, "llm"),
        llm_timeout_s=float(getattr(engine, "llm_timeout_s", 15.0)),
        build_prompt_fn=build_reasoning_prompt,
        dry_run_builder_fn=getattr(engine, "_build_dry_run_answer_from_parts"),
        create_reasoning_plan_fn=create_reasoning_plan_impl,
        build_reasoning_execution_policy_fn=build_reasoning_execution_policy_impl,
        build_controlled_plan_steps_fn=build_controlled_plan_steps,
        build_bounded_plan_steps_with_loop_guard_fn=_build_bounded_plan_steps_with_loop_guard,
        execute_plan_steps_fn=execute_plan_steps_impl,
        apply_tool_safety_runtime_guard_fn=apply_tool_safety_runtime_guard,
        build_multi_agent_coordination_plan_for_runtime_fn=_build_multi_agent_coordination_plan_for_runtime,
        enrich_step_results_with_multi_agent_contract_fn=_enrich_step_results_with_multi_agent_contract,
        build_fallback_planner_observations_fn=_build_fallback_planner_observations,
        build_fallback_answer_response_fn=_build_fallback_answer_response,
        apply_fallback_response_diagnostics_fn=_apply_fallback_response_diagnostics,
        confidence_fn=compute_confidence,
        response_model_cls=AnswerResponse,
        evidence_contract_version=EVIDENCE_CONTRACT_VERSION,
        evidence_summary_fn=getattr(engine, "_evidence_summary"),
        evidence_contract_status_fn=getattr(engine, "_evidence_contract_status"),
        evidence_contract_gate_reason_fn=getattr(engine, "_evidence_contract_gate_reason"),
        self_check_fn=getattr(engine, "_self_check_diagnostics"),
        verify_preflight_fn=getattr(engine, "_verify_diagnostics_preflight"),
        planner_runtime_parity_fn=getattr(engine, "_build_planner_runtime_parity_diagnostics"),
        reasoning_quality_builder_fn=getattr(engine, "_reasoning_quality_diagnostics"),
        reasoning_optimization_builder_fn=getattr(engine, "_build_reasoning_optimization_diagnostics"),
        enterprise_productization_builder_fn=getattr(engine, "_build_enterprise_productization_diagnostics"),
        meta_cognition_builder_fn=getattr(engine, "_build_meta_cognition_diagnostics"),
        warning_flags_applier_fn=_apply_reasoning_runtime_warning_flags,
    )
