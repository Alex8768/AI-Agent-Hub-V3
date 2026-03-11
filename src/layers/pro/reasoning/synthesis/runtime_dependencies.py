from __future__ import annotations

from time import perf_counter

from src.core.config import get_settings
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    AnswerResponse,
)
from src.layers.pro.reasoning.graph.builder import build_reasoning_graph
from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.evaluation.runtime_diagnostics import (
    apply_graph_response_diagnostics as _apply_graph_response_diagnostics,
)
from src.layers.pro.reasoning.evaluation.runtime_productization import (
    build_graph_answer_response as _build_graph_answer_response,
    synthesize_graph_response as _synthesize_graph_response,
    synthesize_with_graph_runtime as _synthesize_with_graph_runtime,
)
from src.layers.pro.reasoning.diagnostics.runtime_contracts import (
    apply_reasoning_runtime_warning_flags as _apply_reasoning_runtime_warning_flags,
)


async def synthesize_with_engine_runtime_dependencies(
    *,
    engine: object,
    request: object,
    build_reasoning_execution_policy_fn: object,
    get_runtime_logger_fn: object,
    build_reasoning_graph_fn: object | None = None,
) -> object:
    build_reasoning_graph_impl = build_reasoning_graph_fn or build_reasoning_graph
    return await _synthesize_with_graph_runtime(
        request=request,
        llm=getattr(engine, "llm"),
        retriever=getattr(engine, "retriever"),
        build_reasoning_graph_fn=build_reasoning_graph_impl,
        run_graph_runtime_fn=getattr(engine, "_run_graph_runtime"),
        synthesize_fallback_fn=getattr(engine, "_synthesize_fallback"),
        get_settings_fn=get_settings,
        agent_state_cls=AgentState,
        synthesize_graph_response_fn=_synthesize_graph_response,
        build_dry_run_answer_fn=getattr(engine, "_build_dry_run_answer"),
        build_graph_answer_response_fn=_build_graph_answer_response,
        apply_graph_response_diagnostics_fn=_apply_graph_response_diagnostics,
        confidence_fn=compute_confidence,
        response_model_cls=AnswerResponse,
        evidence_contract_version=EVIDENCE_CONTRACT_VERSION,
        evidence_summary_fn=getattr(engine, "_evidence_summary"),
        evidence_contract_status_fn=getattr(engine, "_evidence_contract_status"),
        evidence_contract_gate_reason_fn=getattr(engine, "_evidence_contract_gate_reason"),
        self_check_fn=getattr(engine, "_self_check_diagnostics"),
        verify_preflight_fn=getattr(engine, "_verify_diagnostics_preflight"),
        planner_runtime_parity_fn=getattr(engine, "_build_planner_runtime_parity_diagnostics"),
        execution_policy_builder_fn=build_reasoning_execution_policy_fn,
        reasoning_quality_builder_fn=getattr(engine, "_reasoning_quality_diagnostics"),
        reasoning_optimization_builder_fn=getattr(engine, "_build_reasoning_optimization_diagnostics"),
        enterprise_productization_builder_fn=getattr(engine, "_build_enterprise_productization_diagnostics"),
        meta_cognition_builder_fn=getattr(engine, "_build_meta_cognition_diagnostics"),
        warning_flags_applier_fn=_apply_reasoning_runtime_warning_flags,
        perf_counter_fn=perf_counter,
        logger_getter_fn=get_runtime_logger_fn,
    )
