"""Runtime evaluation diagnostics helpers extracted from reasoning engine."""

from __future__ import annotations

from src.layers.pro.reasoning.evaluation.benchmark_registry import (
    build_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.evaluation.benchmark_runner import (
    run_reasoning_benchmark_suite,
)
from src.layers.pro.reasoning.quality_claims import extract_claims
from src.layers.pro.reasoning.quality_confidence import compute_reasoning_quality_confidence
from src.layers.pro.reasoning.quality_coverage import score_claim_coverage
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry
from src.layers.pro.reasoning.trace.trace_collector import collect_reasoning_trace


def reasoning_quality_diagnostics(
    *,
    answer_text: str,
    provenance: list,
    contract: dict[str, object],
    max_retries: int,
    retry_decider: object = decide_reasoning_quality_retry,
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
    retry = retry_decider(
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


def build_reasoning_trace_diagnostics(
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


def build_reasoning_benchmark_diagnostics(
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


def build_runtime_step_results_from_planner_actions(
    *,
    planner_actions: list[str],
    answer_text: str,
    verify: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    actions = [str(x or "") for x in list(planner_actions or [])]
    verify_status = str(verify.get("status", "") or "")
    verify_reasons = list(verify.get("reasons") or [])
    for idx, description in enumerate(actions):
        step_output = answer_text if idx == len(actions) - 1 else description
        rows.append(
            {
                "step_index": int(idx),
                "step_description": str(description or ""),
                "reasoning_output": str(step_output or ""),
                "verify_status": verify_status,
                "verify_reasons": verify_reasons,
            }
        )
    return rows


def build_fallback_planner_observations(
    *,
    planner_step_results: list[dict[str, object]],
) -> dict[str, object]:
    rows = [dict(x or {}) for x in list(planner_step_results or [])]
    planner_step_count = int(len(rows))
    planner_current_step = int(max(planner_step_count - 1, 0)) if planner_step_count > 0 else 0
    planner_current_action = "ANSWER" if planner_step_count > 0 else ""
    fallback_plan_steps = [
        str((row or {}).get("step_description", "") or "")
        for row in rows
    ]
    return {
        "planner_step_count": planner_step_count,
        "planner_current_step": planner_current_step,
        "planner_current_action": planner_current_action,
        "fallback_plan_steps": fallback_plan_steps,
    }


def apply_fallback_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
    warnings: list[str],
    fallback_reason: str | None,
    planner_current_action: str,
    planner_current_step: int,
    provenance: list,
    answer_text: str,
    request_query: str,
    fallback_plan_steps: list[str],
    planner_step_results: list[dict[str, object]],
    evidence_contract_version: str,
    evidence_summary_fn: object,
    evidence_contract_status_fn: object,
    evidence_contract_gate_reason_fn: object,
    self_check_fn: object,
    verify_preflight_fn: object,
    planner_runtime_parity_fn: object,
    execution_policy_builder: object,
    reasoning_quality_builder: object,
    reasoning_optimization_builder: object,
    enterprise_productization_builder: object,
    meta_cognition_builder: object,
    warning_flags_applier: object,
) -> tuple[dict[str, object], list[str]]:
    diag = dict(diagnostics or {})
    diag["fallback_reason"] = fallback_reason
    diag.setdefault("agent_current_action", str(planner_current_action or ""))
    diag.setdefault("agent_current_step", int(planner_current_step or 0))
    diag.setdefault("planner_path_used", False)
    diag.setdefault("evidence_summary", evidence_summary_fn(provenance))
    diag.setdefault("evidence_contract_version", str(evidence_contract_version or ""))
    contract = dict(evidence_contract_status_fn(provenance) or {})
    diag.setdefault("evidence_contract", contract)
    diag.setdefault("evidence_contract_valid_minimal", bool(contract.get("valid_minimal", False)))
    diag.setdefault("evidence_contract_missing_minimal_fields", list(contract.get("missing_minimal_fields") or []))
    diag.setdefault("evidence_contract_missing_minimal_count", int(len(contract.get("missing_minimal_fields") or [])))
    diag.setdefault("evidence_contract_minimal_coverage_score", float(contract.get("minimal_coverage_score") or 0.0))
    diag.setdefault("evidence_contract_gate_reason", evidence_contract_gate_reason_fn(contract))
    diag.setdefault("self_check", self_check_fn(contract))
    execution_policy = execution_policy_builder()
    diag.setdefault("reasoning_execution_policy", dict(execution_policy))
    diag.setdefault(
        "reasoning_quality",
        reasoning_quality_builder(
            answer_text=answer_text,
            provenance=provenance,
            contract=contract,
            max_retries=int(execution_policy.get("max_retries", 0) or 0),
        ),
    )
    self_check = dict(diag.get("self_check") or {})
    diag.setdefault(
        "verify",
        verify_preflight_fn(
            planner_path_used=False,
            self_check=self_check,
        ),
    )
    verify = dict(diag.get("verify") or {})
    diag.setdefault(
        "planner_runtime_parity",
        planner_runtime_parity_fn(
            planner_path_used=False,
            planner_step_count=int(len(fallback_plan_steps)),
            observed_action=str(diag.get("agent_current_action", "") or ""),
            observed_step=int(diag.get("agent_current_step", 0) or 0),
        ),
    )
    diag.setdefault(
        "reasoning_trace",
        build_reasoning_trace_diagnostics(
            query=str(request_query or ""),
            answer_text=answer_text,
            quality=dict(diag.get("reasoning_quality") or {}),
            plan_steps=fallback_plan_steps,
            step_results=list(planner_step_results or []),
        ),
    )
    diag.setdefault(
        "reasoning_benchmark",
        build_reasoning_benchmark_diagnostics(
            suite_name="reasoning_runtime_fallback",
            step_results=list(planner_step_results or []),
        ),
    )
    diag.setdefault(
        "reasoning_optimization",
        reasoning_optimization_builder(
            diagnostics=diag,
            warnings=list(warnings or []),
        ),
    )
    diag.setdefault(
        "enterprise_productization",
        enterprise_productization_builder(
            diagnostics=diag,
            warnings=list(warnings or []),
        ),
    )
    diag.setdefault(
        "meta_cognition",
        meta_cognition_builder(
            diagnostics=diag,
            warnings=list(warnings or []),
        ),
    )
    diag.setdefault(
        "reasoning_timeline",
        dict((dict(diag.get("reasoning_trace") or {}).get("timeline") or {})),
    )
    runtime_warnings = warning_flags_applier(
        warnings=list(warnings or []),
        verify=verify,
        self_check=self_check,
        contract=contract,
    )
    return diag, runtime_warnings


def apply_graph_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
    warnings: list[str],
    iteration_count: int,
    planner_actions: list[str],
    planner_current_action: str,
    planner_current_step: int,
    session_id: str,
    provenance: list,
    answer_text: str,
    request_query: str,
    evidence_contract_version: str,
    evidence_summary_fn: object,
    evidence_contract_status_fn: object,
    evidence_contract_gate_reason_fn: object,
    self_check_fn: object,
    verify_preflight_fn: object,
    planner_runtime_parity_fn: object,
    execution_policy_builder: object,
    reasoning_quality_builder: object,
    reasoning_optimization_builder: object,
    enterprise_productization_builder: object,
    meta_cognition_builder: object,
    warning_flags_applier: object,
) -> tuple[dict[str, object], list[str]]:
    diag = dict(diagnostics or {})
    diag["agent_iterations"] = int(iteration_count or 0)
    diag["agent_actions"] = list(planner_actions or [])
    diag["agent_current_action"] = str(planner_current_action or "")
    diag["agent_current_step"] = int(planner_current_step or 0)
    diag["planner_path_used"] = True
    diag["session_id"] = str(session_id or "")
    diag["evidence_summary"] = evidence_summary_fn(provenance)
    diag["evidence_contract_version"] = str(evidence_contract_version or "")
    contract = dict(evidence_contract_status_fn(provenance) or {})
    diag["evidence_contract"] = contract
    diag["evidence_contract_valid_minimal"] = bool(contract.get("valid_minimal", False))
    diag["evidence_contract_missing_minimal_fields"] = list(contract.get("missing_minimal_fields") or [])
    diag["evidence_contract_missing_minimal_count"] = int(len(contract.get("missing_minimal_fields") or []))
    diag["evidence_contract_minimal_coverage_score"] = float(contract.get("minimal_coverage_score") or 0.0)
    diag["evidence_contract_gate_reason"] = evidence_contract_gate_reason_fn(contract)
    self_check = dict(self_check_fn(contract) or {})
    diag["self_check"] = self_check
    execution_policy = execution_policy_builder()
    diag["reasoning_execution_policy"] = dict(execution_policy)
    diag["reasoning_quality"] = reasoning_quality_builder(
        answer_text=answer_text,
        provenance=provenance,
        contract=contract,
        max_retries=int(execution_policy.get("max_retries", 0) or 0),
    )
    diag["verify"] = verify_preflight_fn(
        planner_path_used=True,
        self_check=self_check,
    )
    verify = dict(diag.get("verify") or {})
    diag["planner_runtime_parity"] = planner_runtime_parity_fn(
        planner_path_used=True,
        planner_step_count=int(len(planner_actions)),
        observed_action=str(diag.get("agent_current_action", "") or ""),
        observed_step=int(diag.get("agent_current_step", 0) or 0),
    )
    per_step_results = build_runtime_step_results_from_planner_actions(
        planner_actions=list(planner_actions or []),
        answer_text=answer_text,
        verify=verify,
    )
    diag["reasoning_trace"] = build_reasoning_trace_diagnostics(
        query=str(request_query or ""),
        answer_text=answer_text,
        quality=dict(diag.get("reasoning_quality") or {}),
        plan_steps=list(planner_actions or []),
        step_results=per_step_results,
    )
    diag["reasoning_benchmark"] = build_reasoning_benchmark_diagnostics(
        suite_name="reasoning_runtime_graph",
        step_results=per_step_results,
    )
    diag["reasoning_optimization"] = reasoning_optimization_builder(
        diagnostics=diag,
        warnings=list(warnings or []),
    )
    diag["enterprise_productization"] = enterprise_productization_builder(
        diagnostics=diag,
        warnings=list(warnings or []),
    )
    diag["meta_cognition"] = meta_cognition_builder(
        diagnostics=diag,
        warnings=list(warnings or []),
    )
    diag["reasoning_timeline"] = dict((dict(diag.get("reasoning_trace") or {}).get("timeline") or {}))
    runtime_warnings = warning_flags_applier(
        warnings=list(warnings or []),
        verify=verify,
        self_check=self_check,
        contract=contract,
    )
    return diag, runtime_warnings
