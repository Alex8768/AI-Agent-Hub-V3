from __future__ import annotations

from dataclasses import dataclass

from src.layers.pro.reasoning.graph.builder import build_reasoning_graph
from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    AnswerRequest,
    AnswerResponse,
)
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.control.loop_guard import (
    build_bounded_plan_steps_with_loop_guard as _build_bounded_plan_steps_with_loop_guard,
)
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps
from src.layers.pro.reasoning.multi_agent.runtime_contracts import (
    build_multi_agent_coordination_plan_for_runtime as _build_multi_agent_coordination_plan_for_runtime,
    enrich_step_results_with_multi_agent_contract as _enrich_step_results_with_multi_agent_contract,
)
from src.layers.pro.reasoning.evaluation.runtime_diagnostics import (
    apply_fallback_response_diagnostics as _apply_fallback_response_diagnostics,
    apply_graph_response_diagnostics as _apply_graph_response_diagnostics,
    build_fallback_planner_observations as _build_fallback_planner_observations,
    build_reasoning_benchmark_diagnostics as _build_reasoning_benchmark_diagnostics,
    build_reasoning_trace_diagnostics as _build_reasoning_trace_diagnostics,
    reasoning_quality_diagnostics as _reasoning_quality_diagnostics,
)
from src.layers.pro.reasoning.evaluation.runtime_productization import (
    build_fallback_answer_response as _build_fallback_answer_response,
    build_fallback_answer_text as _build_fallback_answer_text,
    build_graph_answer_response as _build_graph_answer_response,
    build_dry_run_answer_from_parts as _build_dry_run_answer_from_parts,
    build_dry_run_answer_from_state as _build_dry_run_answer_from_state,
    build_enterprise_productization_diagnostics as _build_enterprise_productization_diagnostics,
    execute_fallback_planner_steps_mvp as _execute_fallback_planner_steps_mvp,
    synthesize_with_graph_runtime as _synthesize_with_graph_runtime,
    synthesize_graph_response as _synthesize_graph_response,
    build_meta_cognition_diagnostics as _build_meta_cognition_diagnostics,
    build_reasoning_optimization_diagnostics as _build_reasoning_optimization_diagnostics,
    run_graph_runtime_with_state_contract as _run_graph_runtime_with_state_contract,
    synthesize_fallback_with_runtime_settings as _synthesize_fallback_with_runtime_settings,
)
from src.layers.pro.reasoning.kernel import build_reasoning_planner_runtime
from src.layers.pro.reasoning.tool_safety.runtime_guard import apply_tool_safety_runtime_guard
from src.layers.pro.reasoning.diagnostics.runtime_contracts import (
    apply_reasoning_runtime_warning_flags as _apply_reasoning_runtime_warning_flags,
    build_planner_runtime_parity_diagnostics as _build_planner_runtime_parity_diagnostics,
    evidence_contract_gate_reason as _evidence_contract_gate_reason,
    evidence_contract_status as _evidence_contract_status,
    evidence_summary as _evidence_summary,
    self_check_diagnostics as _self_check_diagnostics,
    verify_diagnostics_preflight as _verify_diagnostics_preflight,
)
from src.core.config import get_settings

_PLANNER_RUNTIME = build_reasoning_planner_runtime()
create_reasoning_plan = _PLANNER_RUNTIME["create_plan"]
execute_plan_steps = _PLANNER_RUNTIME["execute_steps"]
build_reasoning_prompt = _PLANNER_RUNTIME["build_prompt"]


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro) with agentic loop."""

    retriever: object
    llm: object | None = None
    llm_timeout_s: float = 15.0

    @staticmethod
    def _evidence_summary(provenance: list) -> dict[str, object]:
        return _evidence_summary(provenance)

    @staticmethod
    def _evidence_contract_status(provenance: list) -> dict[str, object]:
        return _evidence_contract_status(provenance)

    @staticmethod
    def _evidence_contract_gate_reason(contract: dict[str, object]) -> str:
        return _evidence_contract_gate_reason(contract)

    @staticmethod
    def _self_check_diagnostics(contract: dict[str, object]) -> dict[str, object]:
        return _self_check_diagnostics(contract)

    @staticmethod
    def _verify_diagnostics_preflight(*, planner_path_used: bool, self_check: dict[str, object]) -> dict[str, object]:
        return _verify_diagnostics_preflight(
            planner_path_used=planner_path_used,
            self_check=self_check,
        )

    @staticmethod
    def _build_planner_runtime_parity_diagnostics(
        *,
        planner_path_used: bool,
        planner_step_count: int,
        observed_action: str,
        observed_step: int,
    ) -> dict[str, object]:
        return _build_planner_runtime_parity_diagnostics(
            planner_path_used=planner_path_used,
            planner_step_count=planner_step_count,
            observed_action=observed_action,
            observed_step=observed_step,
        )

    @staticmethod
    def _reasoning_quality_diagnostics(
        *,
        answer_text: str,
        provenance: list,
        contract: dict[str, object],
        max_retries: int,
    ) -> dict[str, object]:
        return _reasoning_quality_diagnostics(
            answer_text=answer_text,
            provenance=provenance,
            contract=contract,
            max_retries=max_retries,
            retry_decider=decide_reasoning_quality_retry,
        )

    @staticmethod
    def _build_reasoning_trace_diagnostics(
        *,
        query: str,
        answer_text: str,
        quality: dict[str, object],
        plan_steps: list[str],
        step_results: list[dict[str, object]],
    ) -> dict[str, object]:
        return _build_reasoning_trace_diagnostics(
            query=query,
            answer_text=answer_text,
            quality=quality,
            plan_steps=plan_steps,
            step_results=step_results,
        )

    @staticmethod
    def _build_reasoning_benchmark_diagnostics(
        *,
        suite_name: str,
        step_results: list[dict[str, object]],
    ) -> dict[str, object]:
        return _build_reasoning_benchmark_diagnostics(
            suite_name=suite_name,
            step_results=step_results,
        )

    @staticmethod
    def _build_reasoning_optimization_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        return _build_reasoning_optimization_diagnostics(
            diagnostics=diagnostics,
            warnings=warnings,
        )

    @staticmethod
    def _build_enterprise_productization_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        return _build_enterprise_productization_diagnostics(
            diagnostics=diagnostics,
            warnings=warnings,
        )

    @staticmethod
    def _build_meta_cognition_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        return _build_meta_cognition_diagnostics(
            diagnostics=diagnostics,
            warnings=warnings,
        )

    async def _execute_planner_steps_mvp(self, *, request: AnswerRequest) -> list[dict[str, object]]:
        """A2.11 Patch 4: execute deterministic planner steps inside engine fallback."""
        return await _execute_fallback_planner_steps_mvp(
            request=request,
            create_reasoning_plan_fn=create_reasoning_plan,
            build_reasoning_execution_policy_fn=build_reasoning_execution_policy,
            build_controlled_plan_steps_fn=build_controlled_plan_steps,
            build_bounded_plan_steps_with_loop_guard_fn=_build_bounded_plan_steps_with_loop_guard,
            execute_plan_steps_fn=execute_plan_steps,
            apply_tool_safety_runtime_guard_fn=apply_tool_safety_runtime_guard,
            build_multi_agent_coordination_plan_for_runtime_fn=_build_multi_agent_coordination_plan_for_runtime,
            enrich_step_results_with_multi_agent_contract_fn=_enrich_step_results_with_multi_agent_contract,
        )

    async def synthesize(self, request: AnswerRequest) -> AnswerResponse:
        """Synthesize an answer using agentic graph."""
        from time import perf_counter

        return await _synthesize_with_graph_runtime(
            request=request,
            llm=self.llm,
            retriever=self.retriever,
            build_reasoning_graph_fn=build_reasoning_graph,
            run_graph_runtime_fn=self._run_graph_runtime,
            synthesize_fallback_fn=self._synthesize_fallback,
            get_settings_fn=get_settings,
            agent_state_cls=AgentState,
            synthesize_graph_response_fn=_synthesize_graph_response,
            build_dry_run_answer_fn=self._build_dry_run_answer,
            build_graph_answer_response_fn=_build_graph_answer_response,
            apply_graph_response_diagnostics_fn=_apply_graph_response_diagnostics,
            confidence_fn=compute_confidence,
            response_model_cls=AnswerResponse,
            evidence_contract_version=EVIDENCE_CONTRACT_VERSION,
            evidence_summary_fn=self._evidence_summary,
            evidence_contract_status_fn=self._evidence_contract_status,
            evidence_contract_gate_reason_fn=self._evidence_contract_gate_reason,
            self_check_fn=self._self_check_diagnostics,
            verify_preflight_fn=self._verify_diagnostics_preflight,
            planner_runtime_parity_fn=self._build_planner_runtime_parity_diagnostics,
            execution_policy_builder_fn=build_reasoning_execution_policy,
            reasoning_quality_builder_fn=self._reasoning_quality_diagnostics,
            reasoning_optimization_builder_fn=self._build_reasoning_optimization_diagnostics,
            enterprise_productization_builder_fn=self._build_enterprise_productization_diagnostics,
            meta_cognition_builder_fn=self._build_meta_cognition_diagnostics,
            warning_flags_applier_fn=_apply_reasoning_runtime_warning_flags,
            perf_counter_fn=perf_counter,
            logger_getter_fn=_get_runtime_logger,
        )

    async def _synthesize_fallback(self, request: AnswerRequest, error: str | None = None) -> AnswerResponse:
        """Fallback к старому однопроходному режиму (если нет LLM или ошибка графа)."""
        return await _synthesize_fallback_with_runtime_settings(
            request=request,
            retriever=self.retriever,
            error=error,
            get_settings_fn=get_settings,
            execute_planner_steps_mvp_fn=self._execute_planner_steps_mvp,
            build_fallback_planner_observations_fn=_build_fallback_planner_observations,
            build_fallback_answer_text_fn=self._build_fallback_answer_text,
            build_fallback_answer_response_fn=_build_fallback_answer_response,
            apply_fallback_response_diagnostics_fn=_apply_fallback_response_diagnostics,
            confidence_fn=compute_confidence,
            response_model_cls=AnswerResponse,
            evidence_contract_version=EVIDENCE_CONTRACT_VERSION,
            evidence_summary_fn=self._evidence_summary,
            evidence_contract_status_fn=self._evidence_contract_status,
            evidence_contract_gate_reason_fn=self._evidence_contract_gate_reason,
            self_check_fn=self._self_check_diagnostics,
            verify_preflight_fn=self._verify_diagnostics_preflight,
            planner_runtime_parity_fn=self._build_planner_runtime_parity_diagnostics,
            execution_policy_builder_fn=build_reasoning_execution_policy,
            reasoning_quality_builder_fn=self._reasoning_quality_diagnostics,
            reasoning_optimization_builder_fn=self._build_reasoning_optimization_diagnostics,
            enterprise_productization_builder_fn=self._build_enterprise_productization_diagnostics,
            meta_cognition_builder_fn=self._build_meta_cognition_diagnostics,
            warning_flags_applier_fn=_apply_reasoning_runtime_warning_flags,
        )

    def _build_dry_run_answer(self, state: AgentState) -> str:
        """Строит dry-run ответ из состояния агента."""
        return _build_dry_run_answer_from_state(state=state)

    def _build_dry_run_answer_from_parts(self, provenance: list, context_preview: str) -> str:
        """Строит dry-run ответ из частей (для fallback)."""
        return _build_dry_run_answer_from_parts(
            provenance=provenance,
            context_preview=context_preview,
        )

    @staticmethod
    async def _run_graph_runtime(*, graph: object, initial_state: AgentState) -> AgentState:
        return await _run_graph_runtime_with_state_contract(
            graph=graph,
            initial_state=initial_state,
            state_model_cls=AgentState,
        )

    async def _build_fallback_answer_text(
        self,
        *,
        request: AnswerRequest,
        context_preview: str,
        provenance: list,
        dry_run: bool,
    ) -> str:
        return await _build_fallback_answer_text(
            llm=self.llm,
            dry_run=dry_run,
            llm_timeout_s=float(self.llm_timeout_s),
            request=request,
            context_preview=context_preview,
            provenance=provenance,
            build_prompt_fn=build_reasoning_prompt,
            dry_run_builder_fn=self._build_dry_run_answer_from_parts,
        )


def _get_runtime_logger():
    from loguru import logger

    return logger

