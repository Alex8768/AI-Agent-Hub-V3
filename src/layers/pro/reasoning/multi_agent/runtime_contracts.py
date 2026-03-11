"""Runtime multi-agent helper seams extracted from reasoning engine."""

from __future__ import annotations

from src.layers.pro.reasoning.multi_agent.arbitration_contract import (
    arbitrate_multi_agent_candidates,
)
from src.layers.pro.reasoning.multi_agent.coordination_model import (
    MultiAgentCoordinationPlan,
    build_multi_agent_coordination_plan,
)
from src.layers.pro.reasoning.multi_agent.handoff_router import route_multi_agent_handoffs


def build_multi_agent_coordination_plan_for_runtime(
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


def enrich_step_results_with_multi_agent_contract(
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
