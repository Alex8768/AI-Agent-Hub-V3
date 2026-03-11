"""Advanced runtime diagnostics extracted from reasoning engine."""

from __future__ import annotations

import asyncio

from src.layers.pro.meta_cognition.gaps import build_gap_map
from src.layers.pro.meta_cognition.reflection import build_reflection_report
from src.layers.pro.meta_cognition.uncertainty import build_uncertainty_summary
from src.layers.pro.reasoning.context_packer import pack_context
from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
from src.layers.pro.reasoning.enterprise.readiness_contract import (
    build_enterprise_readiness_contract_from_diagnostics,
)
from src.layers.pro.reasoning.enterprise.release_gate_model import (
    build_enterprise_release_gate_policy,
)
from src.layers.pro.reasoning.enterprise.rollout_decision_model import (
    decide_enterprise_rollout_action,
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


def build_reasoning_optimization_diagnostics(
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


def build_enterprise_productization_diagnostics(
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


def build_meta_cognition_diagnostics(
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


async def run_graph_runtime_with_state_contract(
    *,
    graph: object,
    initial_state: object,
    state_model_cls: object,
) -> object:
    runtime_graph = graph.compile() if hasattr(graph, "compile") else graph
    if hasattr(runtime_graph, "ainvoke"):
        raw_state = await runtime_graph.ainvoke(initial_state)
    elif hasattr(runtime_graph, "invoke"):
        raw_state = await asyncio.to_thread(runtime_graph.invoke, initial_state)
    else:
        raise RuntimeError("Reasoning graph runtime does not support invoke/ainvoke")

    if isinstance(raw_state, state_model_cls):
        return raw_state
    if isinstance(raw_state, dict):
        return state_model_cls.model_validate(raw_state)
    raise RuntimeError(f"Unsupported final state type: {type(raw_state).__name__}")


async def build_fallback_answer_text(
    *,
    llm: object | None,
    dry_run: bool,
    llm_timeout_s: float,
    request: object,
    context_preview: str,
    provenance: list,
    build_prompt_fn: object,
    dry_run_builder_fn: object,
) -> str:
    if llm is not None and not dry_run:
        prompt = build_prompt_fn(
            request,
            context_preview=context_preview,
            provenance=provenance,
        )
        try:
            return await asyncio.wait_for(
                llm.generate(prompt),
                timeout=float(llm_timeout_s),
            )
        except Exception:
            return "(reasoning layer stub)"
    if dry_run:
        return str(dry_run_builder_fn(provenance, context_preview))
    return "(reasoning layer stub)"


async def execute_fallback_planner_steps_mvp(
    *,
    request: object,
    create_reasoning_plan_fn: object,
    build_reasoning_execution_policy_fn: object,
    build_controlled_plan_steps_fn: object,
    build_bounded_plan_steps_with_loop_guard_fn: object,
    execute_plan_steps_fn: object,
    apply_tool_safety_runtime_guard_fn: object,
    build_multi_agent_coordination_plan_for_runtime_fn: object,
    enrich_step_results_with_multi_agent_contract_fn: object,
) -> list[dict[str, object]]:
    plan = create_reasoning_plan_fn(query=str(getattr(request, "query", "") or ""))
    policy = build_reasoning_execution_policy_fn()
    controlled_steps = build_controlled_plan_steps_fn(plan=plan, policy=policy)
    bounded_steps = build_bounded_plan_steps_with_loop_guard_fn(
        controlled_steps=controlled_steps,
        max_visits_per_signature=max(int(policy.get("max_retries", 0)) + 1, 1),
    )
    bounded_plan = {"steps": bounded_steps}

    async def _run_reasoning_step(step: dict[str, str]) -> str:
        return str(step.get("description", "") or "")

    async def _run_verify_step(reasoning_output: str) -> dict[str, object]:
        _ = reasoning_output
        return {"status": "pass", "reasons": []}

    step_results = await execute_plan_steps_fn(
        plan=bounded_plan,
        run_reasoning_step=_run_reasoning_step,
        run_verify_step=_run_verify_step,
        max_steps=int(policy.get("max_steps", 0) or 0),
    )
    step_results = apply_tool_safety_runtime_guard_fn(step_results=list(step_results or []))
    plan_steps = [
        str((row or {}).get("description", "") or "")
        for row in list(bounded_plan.get("steps") or [])
    ]
    coordination_plan = build_multi_agent_coordination_plan_for_runtime_fn(
        step_descriptions=plan_steps,
        query=str(getattr(request, "query", "") or ""),
    )
    return enrich_step_results_with_multi_agent_contract_fn(
        step_results=list(step_results or []),
        coordination_plan=coordination_plan,
    )


async def synthesize_fallback_response(
    *,
    request: object,
    retriever: object,
    dry_run: bool,
    fallback_reason: str,
    execute_planner_steps_mvp_fn: object,
    build_fallback_planner_observations_fn: object,
    build_fallback_answer_text_fn: object,
    build_fallback_answer_response_fn: object,
    apply_fallback_response_diagnostics_fn: object,
    confidence_fn: object,
    response_model_cls: object,
    evidence_contract_version: str,
    evidence_summary_fn: object,
    evidence_contract_status_fn: object,
    evidence_contract_gate_reason_fn: object,
    self_check_fn: object,
    verify_preflight_fn: object,
    planner_runtime_parity_fn: object,
    execution_policy_builder_fn: object,
    reasoning_quality_builder_fn: object,
    reasoning_optimization_builder_fn: object,
    enterprise_productization_builder_fn: object,
    meta_cognition_builder_fn: object,
    warning_flags_applier_fn: object,
) -> object:
    result = await retriever.retrieve(request)
    provenance, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)
    context_preview, _ = pack_context(
        preview_items,
        max_chars=int(getattr(request, "max_context_chars", 12000)),
    )
    if not context_preview:
        context_preview = str(getattr(request, "session_memory_last_answer", "") or "")

    planner_step_results = await execute_planner_steps_mvp_fn(request=request)
    planner_observations = build_fallback_planner_observations_fn(
        planner_step_results=list(planner_step_results or []),
    )
    planner_current_step = int(planner_observations.get("planner_current_step", 0) or 0)
    planner_current_action = str(planner_observations.get("planner_current_action", "") or "")
    fallback_plan_steps = [str(x or "") for x in list(planner_observations.get("fallback_plan_steps") or [])]

    answer_text = await build_fallback_answer_text_fn(
        request=request,
        context_preview=context_preview,
        provenance=provenance,
        dry_run=dry_run,
    )
    resp = build_fallback_answer_response_fn(
        answer_text=answer_text,
        context_preview=context_preview,
        provenance=provenance,
        used_chunks=used_chunks,
        used_nodes=used_nodes,
        used_edges=used_edges,
        confidence_fn=confidence_fn,
        response_model_cls=response_model_cls,
    )
    diag, runtime_warnings = apply_fallback_response_diagnostics_fn(
        response=resp,
        fallback_reason=fallback_reason,
        planner_current_action=planner_current_action,
        planner_current_step=planner_current_step,
        provenance=provenance,
        answer_text=answer_text,
        request_query=str(getattr(request, "query", "") or ""),
        fallback_plan_steps=fallback_plan_steps,
        planner_step_results=list(planner_step_results or []),
        evidence_contract_version=evidence_contract_version,
        evidence_summary_fn=evidence_summary_fn,
        evidence_contract_status_fn=evidence_contract_status_fn,
        evidence_contract_gate_reason_fn=evidence_contract_gate_reason_fn,
        self_check_fn=self_check_fn,
        verify_preflight_fn=verify_preflight_fn,
        planner_runtime_parity_fn=planner_runtime_parity_fn,
        execution_policy_builder=execution_policy_builder_fn,
        reasoning_quality_builder=reasoning_quality_builder_fn,
        reasoning_optimization_builder=reasoning_optimization_builder_fn,
        enterprise_productization_builder=enterprise_productization_builder_fn,
        meta_cognition_builder=meta_cognition_builder_fn,
        warning_flags_applier=warning_flags_applier_fn,
    )
    resp.warnings = list(runtime_warnings or [])
    resp.diagnostics = diag
    return resp


def _build_dry_run_answer_core(*, provenance: list, context_preview: str) -> str:
    ids = []
    for item in provenance[:5]:
        try:
            ids.append(f"{item.type}:{item.id}")
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
        for row in ids:
            parts.append(f"- {row}")

    return "\n".join(parts)


def build_dry_run_answer_from_state(*, state: object) -> str:
    provenance = list(getattr(state, "provenance", []) or [])
    context_preview = str(getattr(state, "context_preview", "") or "")
    return _build_dry_run_answer_core(
        provenance=provenance,
        context_preview=context_preview,
    )


def build_dry_run_answer_from_parts(*, provenance: list, context_preview: str) -> str:
    return _build_dry_run_answer_core(
        provenance=list(provenance or []),
        context_preview=str(context_preview or ""),
    )


def build_graph_answer_response(
    *,
    final_state: object,
    answer_text: str,
    confidence_fn: object,
    response_model_cls: object,
) -> object:
    provenance = list(getattr(final_state, "provenance", []) or [])
    confidence = float(confidence_fn(provenance))
    return response_model_cls(
        answer=answer_text,
        confidence=confidence,
        context_preview=str(getattr(final_state, "context_preview", "") or ""),
        provenance=provenance,
        used_chunks=list(getattr(final_state, "used_chunks", []) or []),
        used_nodes=list(getattr(final_state, "used_nodes", []) or []),
        used_edges=list(getattr(final_state, "used_edges", []) or []),
    )


def build_fallback_answer_response(
    *,
    answer_text: str,
    context_preview: str,
    provenance: list,
    used_chunks: list,
    used_nodes: list,
    used_edges: list,
    confidence_fn: object,
    response_model_cls: object,
) -> object:
    normalized_provenance = list(provenance or [])
    confidence = float(confidence_fn(normalized_provenance))
    return response_model_cls(
        answer=answer_text,
        confidence=confidence,
        context_preview=str(context_preview or ""),
        provenance=normalized_provenance,
        used_chunks=[c for c in list(used_chunks or []) if c],
        used_nodes=[n for n in list(used_nodes or []) if n],
        used_edges=[e for e in list(used_edges or []) if e],
    )
