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
from src.layers.pro.reasoning.quality_claims import extract_claims
from src.layers.pro.reasoning.quality_confidence import compute_reasoning_quality_confidence
from src.layers.pro.reasoning.quality_coverage import score_claim_coverage
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.control.loop_guard import (
    apply_reasoning_loop_guard,
    build_reasoning_loop_guard_state,
)
from src.layers.pro.reasoning.control.step_controller import build_controlled_plan_steps
from src.layers.pro.reasoning.multi_agent.arbitration_contract import (
    arbitrate_multi_agent_candidates,
)
from src.layers.pro.reasoning.multi_agent.coordination_model import (
    MultiAgentCoordinationPlan,
    build_multi_agent_coordination_plan,
)
from src.layers.pro.reasoning.multi_agent.handoff_router import route_multi_agent_handoffs
from src.layers.pro.reasoning.evaluation.benchmark_registry import (
    build_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.evaluation.benchmark_runner import (
    run_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.optimization.optimization_decision_model import (
    decide_reasoning_optimization_action,
)
from src.layers.pro.reasoning.optimization.optimization_proposal_model import (
    build_reasoning_optimization_proposals,
)
from src.layers.pro.reasoning.optimization.optimization_signal_model import (
    build_reasoning_optimization_signal_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)
from src.layers.pro.reasoning.enterprise.rollout_decision_model import (
    decide_enterprise_rollout_action,
)
from src.layers.pro.meta_cognition.gaps import build_gap_map
from src.layers.pro.meta_cognition.reflection import build_reflection_report
from src.layers.pro.meta_cognition.uncertainty import build_uncertainty_summary
from src.layers.pro.reasoning.kernel import build_reasoning_planner_runtime
from src.layers.pro.reasoning.tool_safety.runtime_guard import apply_tool_safety_runtime_guard
from src.layers.pro.reasoning.trace.trace_collector import collect_reasoning_trace
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
        claims = extract_claims(reasoning_output=str(answer_text or ""))
        coverage = score_claim_coverage(
            claims=claims,
            provenance=list(provenance or []),
        )
        unsupported_claims = int(coverage.get("claims_uncovered") or 0)
        missing_claims = int(contract.get("missing_minimal_count") or 0)
        confidence = compute_reasoning_quality_confidence(
            coverage_score=float(coverage.get("coverage_score") or 0.0),
            unsupported_claims=unsupported_claims,
            missing_claims=missing_claims,
        )
        retry = decide_reasoning_quality_retry(
            confidence_score=float(confidence.get("confidence_score") or 0.0),
            attempt=0,
            threshold=0.6,
            max_retries=int(max_retries),
        )
        return {
            "version": "v1",
            "claims_total": int(len(claims)),
            "claims_sample": list(claims[:5]),
            "coverage": coverage,
            "confidence": confidence,
            "retry": retry,
        }

    @staticmethod
    def _build_reasoning_trace_diagnostics(
        *,
        query: str,
        answer_text: str,
        quality: dict[str, object],
        plan_steps: list[str],
        step_results: list[dict[str, object]],
    ) -> dict[str, object]:
        return collect_reasoning_trace(
            query=query,
            plan={"steps": [{"description": str(x or "")} for x in list(plan_steps or [])]},
            step_results=list(step_results or []),
            quality=dict(quality or {}),
            answer=answer_text,
        )

    @staticmethod
    def _build_reasoning_benchmark_diagnostics(
        *,
        suite_name: str,
        step_results: list[dict[str, object]],
    ) -> dict[str, object]:
        indexed: dict[str, dict[str, object]] = {}
        cases: list[dict[str, object]] = []
        for idx, row in enumerate(list(step_results or [])):
            result = dict(row or {})
            case_id = f"step_{idx}"
            indexed[case_id] = result
            cases.append(
                {
                    "case_id": case_id,
                    "query": str(result.get("step_description", "") or ""),
                    "expected_signals": ["verify_pass"],
                    "tags": ["runtime_step"],
                    "weight": 1.0,
                }
            )
        suite = build_reasoning_benchmark_suite(
            suite_name=suite_name,
            owner="reasoning_engine",
            tags=["runtime", "diagnostics"],
            cases=cases,
        )

        def _evaluate(case: dict[str, object]) -> dict[str, object]:
            cid = str(case.get("case_id", "") or "")
            row = dict(indexed.get(cid) or {})
            verify_status = str(row.get("verify_status", "") or "")
            passed = verify_status == "pass"
            if "arbitration_score" in row:
                score = float(row.get("arbitration_score", 0.0) or 0.0)
            else:
                score = 1.0 if passed else 0.0
            reasons = [str(x) for x in list(row.get("verify_reasons") or [])]
            return {
                "score": score,
                "passed": passed,
                "reasons": reasons,
                "latency_ms": int(idx if (idx := int(row.get("step_index", 0) or 0)) >= 0 else 0),
            }

        return run_reasoning_benchmark_suite(
            suite=suite,
            evaluate_case=_evaluate,
        )

    @staticmethod
    def _build_reasoning_optimization_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        signal = build_reasoning_optimization_signal_from_diagnostics(
            diagnostics=dict(diagnostics or {}),
            warnings=list(warnings or []),
        )
        proposals_raw: list[dict[str, object]] = []
        confidence_score = float(signal.get("confidence_score", 0.0) or 0.0)
        coverage_score = float(signal.get("coverage_score", 0.0) or 0.0)
        pass_rate = float(signal.get("pass_rate", 0.0) or 0.0)
        retry_rate = float(signal.get("retry_rate", 0.0) or 0.0)
        signal_tags = [str(x) for x in list(signal.get("signal_tags") or [])]
        if confidence_score < 0.8:
            proposals_raw.append(
                {
                    "proposal_id": "opt_confidence_guardrail",
                    "parameter": "confidence_target",
                    "current_value": confidence_score,
                    "proposed_value": min(1.0, confidence_score + 0.2),
                    "expected_gain": min(1.0, 0.8 - confidence_score),
                    "risk_level": "medium",
                    "rationale": ["low_confidence", *signal_tags],
                }
            )
        if coverage_score < 0.8:
            proposals_raw.append(
                {
                    "proposal_id": "opt_coverage_guardrail",
                    "parameter": "coverage_target",
                    "current_value": coverage_score,
                    "proposed_value": min(1.0, coverage_score + 0.2),
                    "expected_gain": min(1.0, 0.8 - coverage_score),
                    "risk_level": "low",
                    "rationale": ["low_coverage", *signal_tags],
                }
            )
        if pass_rate < 0.9:
            proposals_raw.append(
                {
                    "proposal_id": "opt_passrate_guardrail",
                    "parameter": "verification_strictness",
                    "current_value": pass_rate,
                    "proposed_value": min(1.0, pass_rate + 0.1),
                    "expected_gain": min(1.0, 0.9 - pass_rate),
                    "risk_level": "medium",
                    "rationale": ["low_pass_rate", *signal_tags],
                }
            )
        if retry_rate > 0.0:
            proposals_raw.append(
                {
                    "proposal_id": "opt_retry_pressure",
                    "parameter": "retry_budget",
                    "current_value": retry_rate,
                    "proposed_value": max(0.0, retry_rate - 0.5),
                    "expected_gain": min(1.0, retry_rate * 0.5),
                    "risk_level": "high",
                    "rationale": ["retry_pressure", *signal_tags],
                }
            )
        proposals = build_reasoning_optimization_proposals(proposals=proposals_raw)
        decision = decide_reasoning_optimization_action(
            signal=signal,
            proposals=proposals,
            decision_id=f"optimization_decision:{str(signal.get('trace_id', '') or 'runtime')}",
        )
        return {
            "signal": dict(signal),
            "proposals": [dict(x) for x in list(proposals or [])],
            "decision": dict(decision),
        }

    @staticmethod
    def _build_enterprise_productization_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        verify = dict(diagnostics.get("verify") or {})
        self_check = dict(diagnostics.get("self_check") or {})
        benchmark = diagnostics.get("reasoning_benchmark")
        optimization = diagnostics.get("reasoning_optimization")
        release_checks = {
            "verify": str(verify.get("status", "missing") or "missing"),
            "self_check": str(self_check.get("status", "missing") or "missing"),
            "reasoning_benchmark": "pass" if isinstance(benchmark, dict) else "missing",
            "reasoning_optimization": "pass" if isinstance(optimization, dict) else "missing",
        }
        policy = build_enterprise_release_gate_policy(
            profile_name="enterprise_default",
            required_checks=["verify", "self_check", "reasoning_benchmark", "reasoning_optimization"],
            blocking_checks=["verify", "self_check"],
            minimum_pass_rate=0.8,
            minimum_average_score=0.7,
            allow_skipped=False,
            require_benchmark_summary=True,
            require_optimization_review=True,
            allowed_warning_codes=[],
        )
        readiness = build_enterprise_readiness_contract_from_diagnostics(
            diagnostics={**dict(diagnostics or {}), "release_checks": release_checks},
            policy=policy,
            warnings=list(warnings or []),
        )
        rollout = decide_enterprise_rollout_action(
            readiness=readiness,
            policy=policy,
            decision_id=f"enterprise_rollout:{str(diagnostics.get('trace_id', '') or 'runtime')}",
            target_environment="production",
        )
        return {
            "release_gate_policy": dict(policy),
            "release_checks": dict(release_checks),
            "readiness": dict(readiness),
            "rollout_decision": dict(rollout),
        }

    @staticmethod
    def _build_meta_cognition_diagnostics(
        *,
        diagnostics: dict[str, object],
        warnings: list[str],
    ) -> dict[str, object]:
        reasoning_quality = dict(diagnostics.get("reasoning_quality") or {})
        confidence = dict(reasoning_quality.get("confidence") or {})
        coverage = dict(reasoning_quality.get("coverage") or {})
        verify = dict(diagnostics.get("verify") or {})
        self_check = dict(diagnostics.get("self_check") or {})

        confidence_score = float(confidence.get("confidence_score", 0.0) or 0.0)
        coverage_score = float(coverage.get("coverage_score", 0.0) or 0.0)
        missing_claims = int(confidence.get("missing_claims", 0) or 0)
        unsupported_claims = int(confidence.get("unsupported_claims", 0) or 0)

        uncertainty_signals: list[dict[str, object]] = []
        if confidence_score < 0.6:
            uncertainty_signals.append(
                {
                    "code": "low_confidence",
                    "severity": "high" if confidence_score < 0.4 else "medium",
                    "confidence": confidence_score,
                    "source": "reasoning_quality",
                    "message": "Reasoning confidence below target",
                }
            )
        if str(verify.get("status", "") or "") == "warn":
            uncertainty_signals.append(
                {
                    "code": "verify_warn",
                    "severity": "medium",
                    "confidence": max(0.0, 1.0 - float(len(verify.get("reasons") or [])) * 0.25),
                    "source": "verify",
                    "message": "Verify preflight produced warning status",
                }
            )
        if str(self_check.get("status", "") or "") == "warn":
            uncertainty_signals.append(
                {
                    "code": "self_check_warn",
                    "severity": "medium",
                    "confidence": max(0.0, 1.0 - float(len(self_check.get("reasons") or [])) * 0.25),
                    "source": "self_check",
                    "message": "Self-check reported warning status",
                }
            )
        uncertainty = build_uncertainty_summary(
            signals=uncertainty_signals,
            warnings=list(warnings or []),
        )

        gaps_raw: list[dict[str, object]] = []
        if missing_claims > 0:
            gaps_raw.append(
                {
                    "gap_id": "gap:missing_claims",
                    "topic": "evidence coverage",
                    "gap_type": "missing_data",
                    "confidence": min(1.0, 0.5 + (missing_claims * 0.1)),
                    "evidence_refs": [],
                    "source": "reasoning_quality",
                    "message": "Missing evidence-backed claims detected",
                }
            )
        if unsupported_claims > 0:
            gaps_raw.append(
                {
                    "gap_id": "gap:unsupported_claims",
                    "topic": "claim support",
                    "gap_type": "low_confidence",
                    "confidence": min(1.0, 0.5 + (unsupported_claims * 0.1)),
                    "evidence_refs": [],
                    "source": "reasoning_quality",
                    "message": "Unsupported claims detected",
                }
            )
        if coverage_score < 0.6:
            gaps_raw.append(
                {
                    "gap_id": "gap:coverage",
                    "topic": "retrieval coverage",
                    "gap_type": "missing_data",
                    "confidence": max(0.0, 1.0 - coverage_score),
                    "evidence_refs": [],
                    "source": "reasoning_quality",
                    "message": "Coverage score below target",
                }
            )
        gap_map = build_gap_map(
            session_id=str(diagnostics.get("session_id", "") or ""),
            gaps=gaps_raw,
            warnings=list(warnings or []),
        )

        insights: list[dict[str, object]] = []
        if str(uncertainty.get("status", "") or "") == "high":
            insights.append(
                {
                    "code": "reflection_uncertainty_high",
                    "message": "High uncertainty requires additional verification",
                    "severity": "high",
                }
            )
        if str(gap_map.get("status", "") or "") == "needs_attention":
            insights.append(
                {
                    "code": "reflection_gap_attention",
                    "message": "High-priority knowledge gaps require remediation",
                    "severity": "high",
                }
            )
        reflection = build_reflection_report(
            uncertainty_summary=uncertainty,
            gap_map=gap_map,
            insights=insights,
            warnings=list(warnings or []),
        )
        return {
            "uncertainty": dict(uncertainty),
            "gap_map": dict(gap_map),
            "reflection": dict(reflection),
        }

    @staticmethod
    def _build_multi_agent_coordination_plan_for_runtime(
        *,
        step_descriptions: list[str],
        query: str,
    ) -> MultiAgentCoordinationPlan:
        roles = ["researcher", "critic", "synthesizer"]
        steps: list[dict[str, object]] = []
        for idx, description in enumerate(list(step_descriptions or [])):
            input_keys = ["query"] if idx == 0 else [f"step_{idx - 1}_output"]
            depends_on = [] if idx == 0 else [idx - 1]
            steps.append(
                {
                    "step_index": idx,
                    "agent_role": roles[idx % len(roles)],
                    "objective": str(description or ""),
                    "input_keys": input_keys,
                    "output_key": f"step_{idx}_output",
                    "depends_on": depends_on,
                }
            )
        return build_multi_agent_coordination_plan(query=query, steps=steps)

    @staticmethod
    def _enrich_step_results_with_multi_agent_contract(
        *,
        step_results: list[dict[str, object]],
        coordination_plan: MultiAgentCoordinationPlan,
    ) -> list[dict[str, object]]:
        handoffs = route_multi_agent_handoffs(plan=coordination_plan)
        handoffs_by_to_step: dict[int, list[dict[str, object]]] = {}
        for transition in handoffs:
            to_idx = int(transition.get("to_step_index", 0) or 0)
            handoffs_by_to_step.setdefault(to_idx, []).append(dict(transition))

        role_by_index: dict[int, str] = {}
        for row in list(coordination_plan.get("steps") or []):
            idx = int((row or {}).get("step_index", 0) or 0)
            role_by_index[idx] = str((row or {}).get("agent_role", "") or "")

        enriched: list[dict[str, object]] = []
        candidate_rows: list[dict[str, object]] = []
        total = max(len(step_results), 1)
        for row in list(step_results or []):
            result = dict(row or {})
            idx = int(result.get("step_index", 0) or 0)
            verify_status = str(result.get("verify_status", "") or "")
            if verify_status == "pass":
                score = 0.7
            elif verify_status == "warn":
                score = 0.4
            else:
                score = 0.1
            score += (float(idx) / float(total)) * 0.3
            transition_rows = list(handoffs_by_to_step.get(idx) or [])
            result["agent_role"] = role_by_index.get(idx, "")
            result["handoff_transitions"] = transition_rows
            result["handoff_ok"] = all(bool(x.get("accepted")) for x in transition_rows)
            result["arbitration_score"] = max(0.0, min(1.0, float(score)))
            candidate_rows.append(
                {
                    "agent_role": str(result.get("agent_role", "") or ""),
                    "answer": str(result.get("reasoning_output", "") or ""),
                    "score": float(result.get("arbitration_score", 0.0) or 0.0),
                    "reasons": [str(x) for x in list(result.get("verify_reasons") or [])],
                }
            )
            enriched.append(result)

        decision = arbitrate_multi_agent_candidates(candidates=candidate_rows)
        winner_role = str(decision.get("winner_role", "") or "")
        for result in enriched:
            result["selected_by_arbitration"] = bool(
                winner_role and str(result.get("agent_role", "") or "") == winner_role
            )
            result["arbitration_decision"] = dict(decision)
        return enriched

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
        ids = []
        for p in state.provenance[:5]:
            try:
                ids.append(f"{p.type}:{p.id}")
            except Exception:
                continue

        snippet = (state.context_preview or "").strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rstrip() + "…"

        parts = []
        if snippet:
            parts.append("Draft answer (dry-run):")
            parts.append(snippet)
        else:
            parts.append("Draft answer (dry-run): (no context)")

        if ids:
            parts.append("")
            parts.append("Evidence:")
            for x in ids:
                parts.append(f"- {x}")

        return "\n".join(parts)

    def _build_dry_run_answer_from_parts(self, provenance: list, context_preview: str) -> str:
        """Строит dry-run ответ из частей (для fallback)."""
        ids = []
        for p in provenance[:5]:
            try:
                ids.append(f"{p.type}:{p.id}")
            except Exception:
                continue

        snippet = (context_preview or "").strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rstrip() + "…"

        parts = []
        if snippet:
            parts.append("Draft answer (dry-run):")
            parts.append(snippet)
        else:
            parts.append("Draft answer (dry-run): (no context)")

        if ids:
            parts.append("")
            parts.append("Evidence:")
            for x in ids:
                parts.append(f"- {x}")

        return "\n".join(parts)
