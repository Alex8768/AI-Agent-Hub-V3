"""LLM planner policy helpers extracted from answer service."""

from __future__ import annotations

_DEFAULT_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def build_llm_planner_policy_contract(
    *,
    allowed_intents: tuple[str, ...] = _DEFAULT_ALLOWED_INTENTS,
) -> dict[str, object]:
    return {
        "mode": "llm_planner_guarded",
        "allow_llm_source": True,
        "allowed_intents": list(allowed_intents),
        "require_plan_id_prefix_match": True,
        "fallback_on_policy_violation": True,
    }


def apply_llm_planner_policy_guards(
    *,
    intent_payload: dict[str, object],
    plan_bundle: dict[str, object],
    llm_planner_bundle: dict[str, object],
    policy_contract: dict[str, object],
    query: str,
    assistant_mode_enabled: bool,
    deterministic_plan_builder: object,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    normalized_intent = dict(intent_payload or {})
    normalized_plan = dict(plan_bundle or {})
    planner = dict(llm_planner_bundle or {})
    policy = dict(policy_contract or {})

    allowed_intents = [str(x).strip() for x in list(policy.get("allowed_intents") or []) if str(x or "").strip()]
    allowed_intent_set = set(allowed_intents)
    violations: list[str] = []
    applied_reason_codes: list[str] = []

    planner_intent = str(planner.get("intent", "") or "")
    plan_intent = str(normalized_plan.get("intent", "") or "")
    plan_id = str(normalized_plan.get("plan_id", "") or "")
    planner_source = str(planner.get("source", "heuristic") or "heuristic")
    require_prefix_match = bool(policy.get("require_plan_id_prefix_match", True))
    fallback_on_violation = bool(policy.get("fallback_on_policy_violation", True))

    if planner_source == "llm" and planner_intent and planner_intent not in allowed_intent_set:
        violations.append("llm_planner_intent_not_allowlisted")
    if planner_source == "llm" and plan_intent and plan_intent not in allowed_intent_set:
        violations.append("llm_plan_intent_not_allowlisted")
    if planner_source == "llm" and require_prefix_match and plan_id and plan_intent and not plan_id.startswith(
        f"plan:{plan_intent}:"
    ):
        violations.append("llm_plan_id_intent_mismatch")

    if violations and fallback_on_violation:
        fallback_intent = dict(normalized_intent)
        fallback_intent["source"] = "heuristic"
        fallback_intent["reason_codes"] = sorted(
            set(
                [str(x) for x in list(fallback_intent.get("reason_codes") or []) if str(x or "").strip()]
                + ["llm_planner_policy_forced_fallback"]
            )
        )
        fallback_plan = deterministic_plan_builder(
            query=query,
            intent_payload=fallback_intent,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        planner = {
            **planner,
            "source": "fallback",
            "status": "fallback",
            "intent": str(fallback_intent.get("intent", "") or ""),
            "plan_id": str(fallback_plan.get("plan_id", "") or ""),
            "reason_codes": sorted(
                set([str(x) for x in list(planner.get("reason_codes") or []) if str(x or "").strip()] + ["llm_planner_policy_forced_fallback"])
            ),
        }
        normalized_intent = fallback_intent
        normalized_plan = fallback_plan
        applied_reason_codes.append("llm_planner_policy_forced_fallback")

    policy_eval = {
        **policy,
        "violations": sorted(set(violations)),
        "applied_reason_codes": sorted(set(applied_reason_codes)),
    }
    return normalized_intent, normalized_plan, planner, policy_eval
