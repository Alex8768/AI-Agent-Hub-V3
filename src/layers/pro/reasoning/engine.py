from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.layers.pro.reasoning.graph.builder import build_reasoning_graph
from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    AnswerRequest,
    AnswerResponse,
)
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
from src.layers.pro.reasoning.context_packer import pack_context
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.control.loop_guard import (
    apply_reasoning_loop_guard,
    build_reasoning_loop_guard_state,
)
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps
from src.layers.pro.reasoning.multi_agent.coordination_model import (
    MultiAgentCoordinationPlan,
)
from src.layers.pro.reasoning.multi_agent.runtime_contracts import (
    build_multi_agent_coordination_plan_for_runtime as _build_multi_agent_coordination_plan_for_runtime,
    enrich_step_results_with_multi_agent_contract as _enrich_step_results_with_multi_agent_contract,
)
from src.layers.pro.reasoning.evaluation.runtime_diagnostics import (
    build_reasoning_benchmark_diagnostics as _build_reasoning_benchmark_diagnostics,
    build_reasoning_trace_diagnostics as _build_reasoning_trace_diagnostics,
    reasoning_quality_diagnostics as _reasoning_quality_diagnostics,
)
from src.layers.pro.reasoning.evaluation.runtime_productization import (
    build_dry_run_answer_from_parts as _build_dry_run_answer_from_parts,
    build_dry_run_answer_from_state as _build_dry_run_answer_from_state,
    build_enterprise_productization_diagnostics as _build_enterprise_productization_diagnostics,
    build_meta_cognition_diagnostics as _build_meta_cognition_diagnostics,
    build_reasoning_optimization_diagnostics as _build_reasoning_optimization_diagnostics,
)
from src.layers.pro.reasoning.kernel import build_reasoning_planner_runtime
from src.layers.pro.reasoning.tool_safety.runtime_guard import apply_tool_safety_runtime_guard
from src.layers.pro.reasoning.diagnostics.runtime_contracts import (
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

    @staticmethod
    def _build_multi_agent_coordination_plan_for_runtime(
        *,
        step_descriptions: list[str],
        query: str,
    ) -> MultiAgentCoordinationPlan:
        return _build_multi_agent_coordination_plan_for_runtime(
            step_descriptions=step_descriptions,
            query=query,
        )

    @staticmethod
    def _enrich_step_results_with_multi_agent_contract(
        *,
        step_results: list[dict[str, object]],
        coordination_plan: MultiAgentCoordinationPlan,
    ) -> list[dict[str, object]]:
        return _enrich_step_results_with_multi_agent_contract(
            step_results=step_results,
            coordination_plan=coordination_plan,
        )

    async def _execute_planner_steps_mvp(self, *, request: AnswerRequest) -> list[dict[str, object]]:
        """A2.11 Patch 4: execute deterministic planner steps inside engine fallback."""
        plan = create_reasoning_plan(query=str(getattr(request, "query", "") or ""))
        policy = build_reasoning_execution_policy()
        controlled_steps = build_controlled_plan_steps(plan=plan, policy=policy)

        loop_guard_state = build_reasoning_loop_guard_state(
            max_visits_per_signature=max(int(policy.get("max_retries", 0)) + 1, 1)
        )
        bounded_steps: list[dict[str, str]] = []
        for row in controlled_steps:
            guard_result = apply_reasoning_loop_guard(
                state=loop_guard_state,
                step_description=row.get("description", ""),
            )
            loop_guard_state = guard_result["state"]
            if bool((guard_result.get("decision") or {}).get("should_stop")):
                break
            bounded_steps.append({"description": str(row.get("description", "") or "")})
        bounded_plan = {"steps": bounded_steps}

        async def _run_reasoning_step(step: dict[str, str]) -> str:
            return str(step.get("description", "") or "")

        async def _run_verify_step(reasoning_output: str) -> dict[str, object]:
            _ = reasoning_output
            return {"status": "pass", "reasons": []}

        step_results = await execute_plan_steps(
            plan=bounded_plan,
            run_reasoning_step=_run_reasoning_step,
            run_verify_step=_run_verify_step,
            max_steps=int(policy.get("max_steps", 0) or 0),
        )
        step_results = apply_tool_safety_runtime_guard(step_results=list(step_results or []))
        plan_steps = [
            str((row or {}).get("description", "") or "")
            for row in list(bounded_plan.get("steps") or [])
        ]
        coordination_plan = self._build_multi_agent_coordination_plan_for_runtime(
            step_descriptions=plan_steps,
            query=str(getattr(request, "query", "") or ""),
        )
        return self._enrich_step_results_with_multi_agent_contract(
            step_results=list(step_results or []),
            coordination_plan=coordination_plan,
        )

    async def synthesize(self, request: AnswerRequest) -> AnswerResponse:
        """Synthesize an answer using agentic graph."""
        from time import perf_counter
        t0 = perf_counter()

        # Если LLM нет, используем старый путь (dry-run или stub)
        if self.llm is None:
            return await self._synthesize_fallback(request)

        # Строим граф
        graph = build_reasoning_graph(self.llm, self.retriever)
        
        # Инициализируем состояние
        initial_state = AgentState(
            query=request.query,
            workspace_id=getattr(request, "workspace_id", "default"),
            session_id=getattr(request, "session_id", "default"),
            session_memory_last_answer=str(getattr(request, "session_memory_last_answer", "") or ""),
            k=request.k,
            graph_depth=request.graph_depth,
            max_context_chars=request.max_context_chars,
            context_preview=str(getattr(request, "session_memory_last_answer", "") or ""),
        )

        # Запускаем граф
        try:
            runtime_graph = graph.compile() if hasattr(graph, "compile") else graph
            if hasattr(runtime_graph, "ainvoke"):
                raw_state = await runtime_graph.ainvoke(initial_state)
            elif hasattr(runtime_graph, "invoke"):
                import asyncio

                raw_state = await asyncio.to_thread(runtime_graph.invoke, initial_state)
            else:
                raise RuntimeError("Reasoning graph runtime does not support invoke/ainvoke")

            # LangGraph runtime may return dict-like state snapshots.
            if isinstance(raw_state, AgentState):
                final_state = raw_state
            elif isinstance(raw_state, dict):
                final_state = AgentState.model_validate(raw_state)
            else:
                raise RuntimeError(f"Unsupported final state type: {type(raw_state).__name__}")
        except Exception as e:
            # В случае ошибки графа - падаем на старый путь
            return await self._synthesize_fallback(request, error=str(e))

        # Safety net: if planner graph produced an internal error marker,
        # fallback to the one-pass path with established timeout/error behavior.
        if getattr(final_state, "error", None):
            return await self._synthesize_fallback(request, error=str(final_state.error))

        # Собираем ответ из финального состояния
        from src.core.config import get_settings
        s = get_settings()
        dry_run = bool(getattr(s, "feature_reasoning_llm_dry_run", False))

        answer_text = final_state.final_answer or "(no answer generated)"
        if dry_run and not final_state.final_answer:
            # Генерируем dry-run ответ из контекста
            answer_text = self._build_dry_run_answer(final_state)

        # Считаем confidence (пока используем старую логику)
        confidence = compute_confidence(final_state.provenance)

        # Контекст для preview (берём из состояния)
        context_preview = final_state.context_preview or ""

        # Собираем результат
        resp = AnswerResponse(
            answer=answer_text,
            confidence=confidence,
            context_preview=context_preview,
            provenance=final_state.provenance,
            used_chunks=final_state.used_chunks,
            used_nodes=final_state.used_nodes,
            used_edges=final_state.used_edges,
        )

        # Добавляем диагностику
        try:
            diag = dict(getattr(resp, "diagnostics", None) or {})
            diag["agent_iterations"] = final_state.iteration_count
            diag["agent_actions"] = final_state.plan
            diag["agent_current_action"] = str(getattr(final_state, "current_action", "") or "")
            diag["agent_current_step"] = int(getattr(final_state, "current_step", 0) or 0)
            diag["planner_path_used"] = True
            diag["session_id"] = str(getattr(final_state, "session_id", "") or "")
            diag["evidence_summary"] = self._evidence_summary(final_state.provenance)
            diag["evidence_contract_version"] = EVIDENCE_CONTRACT_VERSION
            contract = self._evidence_contract_status(final_state.provenance)
            diag["evidence_contract"] = contract
            diag["evidence_contract_valid_minimal"] = bool(contract.get("valid_minimal", False))
            diag["evidence_contract_missing_minimal_fields"] = list(
                contract.get("missing_minimal_fields") or []
            )
            diag["evidence_contract_missing_minimal_count"] = int(
                len(contract.get("missing_minimal_fields") or [])
            )
            diag["evidence_contract_minimal_coverage_score"] = float(
                contract.get("minimal_coverage_score") or 0.0
            )
            diag["evidence_contract_gate_reason"] = self._evidence_contract_gate_reason(contract)
            self_check = self._self_check_diagnostics(contract)
            diag["self_check"] = self_check
            execution_policy = build_reasoning_execution_policy()
            diag["reasoning_execution_policy"] = dict(execution_policy)
            diag["reasoning_quality"] = self._reasoning_quality_diagnostics(
                answer_text=answer_text,
                provenance=final_state.provenance,
                contract=contract,
                max_retries=int(execution_policy.get("max_retries", 0) or 0),
            )
            diag["verify"] = self._verify_diagnostics_preflight(
                planner_path_used=True,
                self_check=self_check,
            )
            verify = dict(diag.get("verify") or {})
            planner_actions = [str(x or "") for x in list(getattr(final_state, "plan", []) or [])]
            diag["planner_runtime_parity"] = self._build_planner_runtime_parity_diagnostics(
                planner_path_used=True,
                planner_step_count=int(len(planner_actions)),
                observed_action=str(diag.get("agent_current_action", "") or ""),
                observed_step=int(diag.get("agent_current_step", 0) or 0),
            )
            per_step_results: list[dict[str, object]] = []
            for idx, description in enumerate(planner_actions):
                step_output = answer_text if idx == len(planner_actions) - 1 else description
                per_step_results.append(
                    {
                        "step_index": int(idx),
                        "step_description": str(description or ""),
                        "reasoning_output": str(step_output or ""),
                        "verify_status": str(verify.get("status", "") or ""),
                        "verify_reasons": list(verify.get("reasons") or []),
                    }
                )
            diag["reasoning_trace"] = self._build_reasoning_trace_diagnostics(
                query=str(getattr(request, "query", "") or ""),
                answer_text=answer_text,
                quality=dict(diag.get("reasoning_quality") or {}),
                plan_steps=planner_actions,
                step_results=per_step_results,
            )
            diag["reasoning_benchmark"] = self._build_reasoning_benchmark_diagnostics(
                suite_name="reasoning_runtime_graph",
                step_results=per_step_results,
            )
            diag["reasoning_optimization"] = self._build_reasoning_optimization_diagnostics(
                diagnostics=diag,
                warnings=list(getattr(resp, "warnings", []) or []),
            )
            diag["enterprise_productization"] = self._build_enterprise_productization_diagnostics(
                diagnostics=diag,
                warnings=list(getattr(resp, "warnings", []) or []),
            )
            diag["meta_cognition"] = self._build_meta_cognition_diagnostics(
                diagnostics=diag,
                warnings=list(getattr(resp, "warnings", []) or []),
            )
            diag["reasoning_timeline"] = dict(
                (dict(diag.get("reasoning_trace") or {}).get("timeline") or {})
            )
            if str(verify.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "verify_warning" not in resp.warnings:
                    resp.warnings.append("verify_warning")
            if str(self_check.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "self_check_warning" not in resp.warnings:
                    resp.warnings.append("self_check_warning")
            if not bool(contract.get("valid_minimal", False)):
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "evidence_contract_minimal_invalid" not in resp.warnings:
                    resp.warnings.append("evidence_contract_minimal_invalid")
            if final_state.error:
                diag["agent_error"] = final_state.error
            resp.diagnostics = diag
        except Exception:
            pass

        # Логируем
        try:
            from loguru import logger
            elapsed_ms = int((perf_counter() - t0) * 1000)
            logger.info(
                "reasoning.agent elapsed_ms={} iterations={} conf={}",
                elapsed_ms,
                final_state.iteration_count,
                float(confidence),
            )
        except Exception:
            pass

        return resp

    async def _synthesize_fallback(self, request: AnswerRequest, error: str | None = None) -> AnswerResponse:
        """Fallback к старому однопроходному режиму (если нет LLM или ошибка графа)."""
        from time import perf_counter
        t0 = perf_counter()

        result = await self.retriever.retrieve(request)

        provenance, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)

        context_preview, _ = pack_context(
            preview_items,
            max_chars=int(getattr(request, "max_context_chars", 12000)),
        )
        if not context_preview:
            # A2.1: keep session continuity when retrieval returns empty context.
            context_preview = str(getattr(request, "session_memory_last_answer", "") or "")

        s = get_settings()
        dry_run = bool(getattr(s, "feature_reasoning_llm_dry_run", False))

        fallback_reason: str | None = error or "fallback"
        planner_step_results = await self._execute_planner_steps_mvp(request=request)
        planner_step_count = int(len(planner_step_results or []))
        planner_current_step = int(max(planner_step_count - 1, 0)) if planner_step_count > 0 else 0
        planner_current_action = "ANSWER" if planner_step_count > 0 else ""

        if self.llm is not None and not dry_run:
            # Пробуем вызвать LLM напрямую (один раз)
            import asyncio

            prompt = build_reasoning_prompt(
                request,
                context_preview=context_preview,
                provenance=provenance,
            )
            try:
                answer_text = await asyncio.wait_for(
                    self.llm.generate(prompt),
                    timeout=float(self.llm_timeout_s),
                )
            except Exception:
                answer_text = "(reasoning layer stub)"
        else:
            if dry_run:
                answer_text = self._build_dry_run_answer_from_parts(provenance, context_preview)
            else:
                answer_text = "(reasoning layer stub)"

        confidence = compute_confidence(provenance)

        resp = AnswerResponse(
            answer=answer_text,
            confidence=confidence,
            context_preview=context_preview,
            provenance=provenance,
            used_chunks=[c for c in used_chunks if c],
            used_nodes=[n for n in used_nodes if n],
            used_edges=[e for e in used_edges if e],
        )

        # Добавляем диагностику
        try:
            diag = dict(getattr(resp, "diagnostics", None) or {})
            diag["fallback_reason"] = fallback_reason
            diag.setdefault("agent_current_action", planner_current_action)
            diag.setdefault("agent_current_step", planner_current_step)
            diag.setdefault("planner_path_used", False)
            diag.setdefault("evidence_summary", self._evidence_summary(provenance))
            diag.setdefault("evidence_contract_version", EVIDENCE_CONTRACT_VERSION)
            contract = self._evidence_contract_status(provenance)
            diag.setdefault("evidence_contract", contract)
            diag.setdefault(
                "evidence_contract_valid_minimal",
                bool(contract.get("valid_minimal", False)),
            )
            diag.setdefault(
                "evidence_contract_missing_minimal_fields",
                list(contract.get("missing_minimal_fields") or []),
            )
            diag.setdefault(
                "evidence_contract_missing_minimal_count",
                int(len(contract.get("missing_minimal_fields") or [])),
            )
            diag.setdefault(
                "evidence_contract_minimal_coverage_score",
                float(contract.get("minimal_coverage_score") or 0.0),
            )
            diag.setdefault(
                "evidence_contract_gate_reason",
                self._evidence_contract_gate_reason(contract),
            )
            diag.setdefault("self_check", self._self_check_diagnostics(contract))
            execution_policy = build_reasoning_execution_policy()
            diag.setdefault("reasoning_execution_policy", dict(execution_policy))
            diag.setdefault(
                "reasoning_quality",
                self._reasoning_quality_diagnostics(
                    answer_text=answer_text,
                    provenance=provenance,
                    contract=contract,
                    max_retries=int(execution_policy.get("max_retries", 0) or 0),
                ),
            )
            self_check = dict(diag.get("self_check") or {})
            diag.setdefault(
                "verify",
                self._verify_diagnostics_preflight(
                    planner_path_used=False,
                    self_check=self_check,
                ),
            )
            verify = dict(diag.get("verify") or {})
            fallback_plan_steps = [
                str((row or {}).get("step_description", "") or "")
                for row in list(planner_step_results or [])
            ]
            diag.setdefault(
                "planner_runtime_parity",
                self._build_planner_runtime_parity_diagnostics(
                    planner_path_used=False,
                    planner_step_count=int(len(fallback_plan_steps)),
                    observed_action=str(diag.get("agent_current_action", "") or ""),
                    observed_step=int(diag.get("agent_current_step", 0) or 0),
                ),
            )
            diag.setdefault(
                "reasoning_trace",
                self._build_reasoning_trace_diagnostics(
                    query=str(getattr(request, "query", "") or ""),
                    answer_text=answer_text,
                    quality=dict(diag.get("reasoning_quality") or {}),
                    plan_steps=fallback_plan_steps,
                    step_results=list(planner_step_results or []),
                ),
            )
            diag.setdefault(
                "reasoning_benchmark",
                self._build_reasoning_benchmark_diagnostics(
                    suite_name="reasoning_runtime_fallback",
                    step_results=list(planner_step_results or []),
                ),
            )
            diag.setdefault(
                "reasoning_optimization",
                self._build_reasoning_optimization_diagnostics(
                    diagnostics=diag,
                    warnings=list(getattr(resp, "warnings", []) or []),
                ),
            )
            diag.setdefault(
                "enterprise_productization",
                self._build_enterprise_productization_diagnostics(
                    diagnostics=diag,
                    warnings=list(getattr(resp, "warnings", []) or []),
                ),
            )
            diag.setdefault(
                "meta_cognition",
                self._build_meta_cognition_diagnostics(
                    diagnostics=diag,
                    warnings=list(getattr(resp, "warnings", []) or []),
                ),
            )
            diag.setdefault(
                "reasoning_timeline",
                dict((dict(diag.get("reasoning_trace") or {}).get("timeline") or {})),
            )
            if str(verify.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "verify_warning" not in resp.warnings:
                    resp.warnings.append("verify_warning")
            if str(self_check.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "self_check_warning" not in resp.warnings:
                    resp.warnings.append("self_check_warning")
            if not bool(contract.get("valid_minimal", False)):
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "evidence_contract_minimal_invalid" not in resp.warnings:
                    resp.warnings.append("evidence_contract_minimal_invalid")
            resp.diagnostics = diag
        except Exception:
            pass

        return resp

    def _build_dry_run_answer(self, state: AgentState) -> str:
        """Строит dry-run ответ из состояния агента."""
        return _build_dry_run_answer_from_state(state=state)

    def _build_dry_run_answer_from_parts(self, provenance: list, context_preview: str) -> str:
        """Строит dry-run ответ из частей (для fallback)."""
        return _build_dry_run_answer_from_parts(
            provenance=provenance,
            context_preview=context_preview,
        )
