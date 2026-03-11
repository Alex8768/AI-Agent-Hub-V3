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


def build_feedback_policy_contract() -> dict[str, object]:
    return {
        "mode": "feedback_learning_guarded",
        "allowed_signals": ["approve", "cancel", "edit"],
        "max_signals_per_request": 3,
        "require_latest_in_signals": True,
        "fallback_on_policy_violation": True,
    }


def apply_feedback_policy_guards(
    *,
    feedback_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    feedback = dict(feedback_bundle or {})
    policy = dict(policy_contract or {})

    allowed_signals = [str(x).strip() for x in list(policy.get("allowed_signals") or []) if str(x).strip()]
    allowed_set = set(allowed_signals)
    max_signals = int(policy.get("max_signals_per_request", 3) or 3)
    require_latest_in_signals = bool(policy.get("require_latest_in_signals", True))
    fallback_on_violation = bool(policy.get("fallback_on_policy_violation", True))

    signals = [str(x).strip() for x in list(feedback.get("signals") or []) if str(x).strip()]
    latest_signal = str(feedback.get("latest_signal", "none") or "none").strip()
    violations: list[str] = []
    applied_reason_codes: list[str] = []

    if any(signal not in allowed_set for signal in signals):
        violations.append("feedback_signal_not_allowlisted")
    if len(signals) > max_signals:
        violations.append("feedback_signals_exceed_max")
    if require_latest_in_signals and latest_signal != "none" and latest_signal not in signals:
        violations.append("feedback_latest_signal_mismatch")

    if violations and fallback_on_violation:
        normalized: list[str] = []
        seen: set[str] = set()
        for signal in signals:
            if signal not in allowed_set or signal in seen:
                continue
            seen.add(signal)
            normalized.append(signal)
            if len(normalized) >= max_signals:
                break
        latest_signal = normalized[-1] if normalized else "none"
        feedback["signals"] = normalized
        feedback["latest_signal"] = latest_signal
        feedback["signal_counts"] = {
            "approve": int(1 if "approve" in normalized else 0),
            "cancel": int(1 if "cancel" in normalized else 0),
            "edit": int(1 if "edit" in normalized else 0),
        }
        reason_codes = [str(x) for x in list(feedback.get("reason_codes") or []) if str(x or "").strip()]
        reason_codes.append("feedback_policy_forced_fallback")
        feedback["reason_codes"] = sorted(set(reason_codes))
        applied_reason_codes.append("feedback_policy_forced_fallback")

    policy_eval = {
        **policy,
        "violations": sorted(set(violations)),
        "applied_reason_codes": sorted(set(applied_reason_codes)),
    }
    return feedback, policy_eval


def build_feedback_adaptation_policy_contract(
    *,
    allowed_intents: tuple[str, ...] = _DEFAULT_ALLOWED_INTENTS,
) -> dict[str, object]:
    return {
        "mode": "feedback_adaptation_guarded",
        "allowed_latest_signals": ["none", "approve", "cancel", "edit"],
        "allowed_intents": list(allowed_intents),
        "max_boosted_intents": 2,
        "max_suppressed_intents": 1,
        "forbid_boost_suppress_overlap": True,
        "fallback_on_policy_violation": True,
    }


def apply_feedback_adaptation_policy_guards(
    *,
    adaptation_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    adaptation = dict(adaptation_bundle or {})
    policy = dict(policy_contract or {})
    allowed_signals = {str(x).strip() for x in list(policy.get("allowed_latest_signals") or []) if str(x).strip()}
    allowed_intents = {str(x).strip() for x in list(policy.get("allowed_intents") or []) if str(x).strip()}
    max_boosted = int(policy.get("max_boosted_intents", 2) or 2)
    max_suppressed = int(policy.get("max_suppressed_intents", 1) or 1)
    fallback_on_violation = bool(policy.get("fallback_on_policy_violation", True))
    forbid_overlap = bool(policy.get("forbid_boost_suppress_overlap", True))

    latest_signal = str(adaptation.get("latest_signal", "none") or "none").strip().lower()
    boosted = [str(x).strip() for x in list(adaptation.get("boosted_intents") or []) if str(x).strip()]
    suppressed = [str(x).strip() for x in list(adaptation.get("suppressed_intents") or []) if str(x).strip()]
    violations: list[str] = []
    applied_reason_codes: list[str] = []

    if latest_signal not in allowed_signals:
        violations.append("feedback_adaptation_latest_signal_not_allowlisted")
    if any(intent not in allowed_intents for intent in boosted):
        violations.append("feedback_adaptation_boosted_intent_not_allowlisted")
    if any(intent not in allowed_intents for intent in suppressed):
        violations.append("feedback_adaptation_suppressed_intent_not_allowlisted")
    if len(boosted) > max_boosted:
        violations.append("feedback_adaptation_boosted_intents_exceed_max")
    if len(suppressed) > max_suppressed:
        violations.append("feedback_adaptation_suppressed_intents_exceed_max")
    if forbid_overlap and (set(boosted) & set(suppressed)):
        violations.append("feedback_adaptation_overlap_detected")

    if violations and fallback_on_violation:
        normalized_boosted: list[str] = []
        seen: set[str] = set()
        for intent in boosted:
            if intent not in allowed_intents or intent in seen:
                continue
            seen.add(intent)
            normalized_boosted.append(intent)
            if len(normalized_boosted) >= max_boosted:
                break

        normalized_suppressed: list[str] = []
        seen_s: set[str] = set()
        for intent in suppressed:
            if intent not in allowed_intents or intent in seen_s:
                continue
            if forbid_overlap and intent in set(normalized_boosted):
                continue
            seen_s.add(intent)
            normalized_suppressed.append(intent)
            if len(normalized_suppressed) >= max_suppressed:
                break

        if latest_signal not in allowed_signals:
            latest_signal = "none"
        if latest_signal == "cancel":
            if not normalized_boosted:
                normalized_boosted = ["general_query"]
            if normalized_suppressed and normalized_suppressed[0] == "general_query":
                normalized_suppressed = []

        adaptation["latest_signal"] = latest_signal
        adaptation["boosted_intents"] = normalized_boosted
        adaptation["suppressed_intents"] = normalized_suppressed
        reason_codes = [str(x) for x in list(adaptation.get("reason_codes") or []) if str(x or "").strip()]
        reason_codes.append("feedback_adaptation_policy_forced_fallback")
        adaptation["reason_codes"] = sorted(set(reason_codes))
        applied_reason_codes.append("feedback_adaptation_policy_forced_fallback")

    policy_eval = {
        **policy,
        "violations": sorted(set(violations)),
        "applied_reason_codes": sorted(set(applied_reason_codes)),
    }
    return adaptation, policy_eval



def build_tool_selection_policy_contract() -> dict[str, object]:
    return {
        "mode": "tool_selection_guarded",
        "allow_mcp_source": True,
        "allow_deterministic_fallback": True,
        "allowed_routes": ["mcp_registry_match", "deterministic_fallback", "diagnostics_only"],
        "require_plan_step_binding": True,
        "max_selected_tools": 5,
        "fallback_on_policy_violation": True,
    }


def apply_tool_selection_policy_guards(
    *,
    tool_selection_bundle: dict[str, object],
    policy_contract: dict[str, object],
    plan_bundle: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    selection = dict(tool_selection_bundle or {})
    policy = dict(policy_contract or {})
    selected = [dict(x or {}) for x in list(selection.get("selected_tools") or [])]
    plan_steps = [dict(x or {}) for x in list(dict(plan_bundle or {}).get("steps") or [])]
    valid_step_ids = {str(x.get("step_id", "") or "") for x in plan_steps if str(x.get("step_id", "") or "")}
    allowed_routes = {str(x).strip() for x in list(policy.get("allowed_routes") or []) if str(x).strip()}
    max_selected_tools = int(policy.get("max_selected_tools", 5) or 5)
    fallback_on_violation = bool(policy.get("fallback_on_policy_violation", True))
    require_step_binding = bool(policy.get("require_plan_step_binding", True))
    allow_mcp_source = bool(policy.get("allow_mcp_source", True))
    allow_deterministic_fallback = bool(policy.get("allow_deterministic_fallback", True))
    source = str(selection.get("source", "none") or "none")

    violations: list[str] = []
    sanitized: list[dict[str, object]] = []
    blocked_step_ids: list[str] = [str(x) for x in list(selection.get("blocked_step_ids") or []) if str(x)]
    for row in selected:
        step_id = str(row.get("step_id", "") or "")
        route = str(row.get("route", "") or "")
        if require_step_binding and step_id and step_id not in valid_step_ids:
            violations.append("tool_selection_step_not_in_plan")
            blocked_step_ids.append(step_id)
            continue
        if route not in allowed_routes:
            violations.append("tool_selection_route_not_allowlisted")
            if step_id:
                blocked_step_ids.append(step_id)
            continue
        sanitized.append(row)

    if source == "mcp" and not allow_mcp_source:
        violations.append("tool_selection_mcp_source_not_allowed")
    if source == "deterministic" and not allow_deterministic_fallback:
        violations.append("tool_selection_fallback_source_not_allowed")
    if len(sanitized) > max_selected_tools:
        violations.append("tool_selection_max_selected_tools_exceeded")
        sanitized = sanitized[:max_selected_tools]

    applied_reason_codes: list[str] = []
    if violations and fallback_on_violation:
        fallback_selected = []
        for step in plan_steps[:max_selected_tools]:
            step_id = str(step.get("step_id", "") or "")
            if not step_id:
                continue
            fallback_selected.append(
                {
                    "step_id": step_id,
                    "tool_name": "none",
                    "route": "deterministic_fallback",
                    "reason": "tool_selection_policy_fallback",
                }
            )
        source = "deterministic"
        sanitized = fallback_selected
        applied_reason_codes.append("tool_selection_policy_forced_fallback")

    reason_codes = [str(x) for x in list(selection.get("reason_codes") or []) if str(x).strip()]
    reason_codes.extend(applied_reason_codes)
    selection["source"] = source
    selection["selected_tools"] = sanitized
    selection["blocked_step_ids"] = sorted(set(blocked_step_ids))
    selection["reason_codes"] = sorted(set(reason_codes))
    policy_eval = {
        **policy,
        "violations": sorted(set(violations)),
        "applied_reason_codes": sorted(set(applied_reason_codes)),
    }
    return selection, policy_eval


def build_transition_policy_contract(
    *,
    max_approved_action_ids: int,
    allowlisted_action_types: tuple[str, ...],
    allowlisted_action_pattern: str,
) -> dict[str, object]:
    return {
        "mode": "confirmation_guarded",
        "require_confirmation_token": True,
        "allow_partial_approval": True,
        "max_approved_action_ids": int(max_approved_action_ids),
        "allowlisted_action_types": list(allowlisted_action_types),
        "allowlisted_action_pattern": str(allowlisted_action_pattern or ""),
        "enforce_allowlisted_action_types": True,
        "allowed_decisions": ["approve", "cancel"],
    }


def apply_plan_policy_guards(
    *,
    plan_bundle: dict[str, object],
    max_steps: int = 5,
) -> tuple[dict[str, object], dict[str, object]]:
    plan = dict(plan_bundle or {})
    rows = [dict(row or {}) for row in list(plan.get("steps") or [])]
    reason_codes: list[str] = []
    blocked_steps_count = 0
    truncated = False

    allowed_steps: list[dict[str, object]] = []
    for row in rows:
        action = str(row.get("action", "") or "")
        action_lower = action.lower()
        is_prepare_draft = action_lower.startswith("prepare_") and action_lower.endswith("_draft")
        has_unsafe_marker = any(x in action_lower for x in ["execute", "delete", "write", "send", "publish"])
        if is_prepare_draft and not has_unsafe_marker:
            allowed_steps.append(row)
            continue
        blocked_steps_count += 1

    if blocked_steps_count:
        reason_codes.append("unsafe_steps_blocked")

    if len(allowed_steps) > int(max_steps):
        allowed_steps = allowed_steps[: int(max_steps)]
        truncated = True
        reason_codes.append("plan_steps_truncated_by_policy")

    status = str(plan.get("status", "idle") or "idle")
    if status == "ready" and not allowed_steps:
        status = "guarded"
        reason_codes.append("plan_guard_blocked_all_steps")

    guarded_plan = {
        **plan,
        "status": status,
        "steps": allowed_steps,
        "requires_confirmation": bool(allowed_steps),
    }
    policy = {
        "mode": "review_only",
        "max_steps": int(max_steps),
        "blocked_steps_count": int(blocked_steps_count),
        "truncated": bool(truncated),
        "allowed_action_pattern": "prepare_*_draft",
        "reason_codes": reason_codes,
    }
    return guarded_plan, policy


def build_assistant_recovery_policy_contract() -> dict[str, object]:
    return {
        "mode": "assistant_chat_recovery_guarded",
        "allow_low_evidence_only": True,
        "allowed_intents": ["general_chat", "general_query"],
        "block_greeting_queries": True,
        "allowed_languages": ["ru", "en"],
        "require_assistant_mode": True,
        "fallback_on_policy_violation": True,
    }


def apply_assistant_recovery_policy_guards(
    *,
    policy_contract: dict[str, object],
    assistant_mode_enabled: bool,
    has_evidence: bool,
    plan_intent: str,
    query: str,
    target_language: str,
    normalize_language_tag_fn: object,
    is_simple_greeting_query_fn: object,
) -> tuple[bool, dict[str, object]]:
    policy = dict(policy_contract or {})
    allowed_intents = {str(x).strip() for x in list(policy.get("allowed_intents") or []) if str(x).strip()}
    allowed_languages = {str(x).strip() for x in list(policy.get("allowed_languages") or []) if str(x).strip()}
    allow_low_evidence_only = bool(policy.get("allow_low_evidence_only", True))
    block_greetings = bool(policy.get("block_greeting_queries", True))
    require_assistant_mode = bool(policy.get("require_assistant_mode", True))
    fallback_on_violation = bool(policy.get("fallback_on_policy_violation", True))

    normalized_intent = str(plan_intent or "general_query").strip() or "general_query"
    if callable(normalize_language_tag_fn):
        normalized_language = str(normalize_language_tag_fn(target_language, query=query) or "")
    else:
        normalized_language = str(target_language or "").strip().lower() or "auto"
    violations: list[str] = []
    applied_reason_codes: list[str] = []

    if require_assistant_mode and not assistant_mode_enabled:
        violations.append("assistant_chat_recovery_assistant_mode_disabled")
    if allow_low_evidence_only and has_evidence:
        violations.append("assistant_chat_recovery_requires_low_evidence")
    if normalized_intent not in allowed_intents:
        violations.append("assistant_chat_recovery_intent_not_allowlisted")
    if block_greetings and callable(is_simple_greeting_query_fn) and bool(is_simple_greeting_query_fn(query)):
        violations.append("assistant_chat_recovery_greeting_blocked")
    if normalized_language not in allowed_languages:
        violations.append("assistant_chat_recovery_language_not_allowlisted")

    allow_recovery = not violations
    if violations and fallback_on_violation:
        allow_recovery = False
        applied_reason_codes.append("assistant_chat_recovery_policy_forced_fallback")

    policy_eval = {
        **policy,
        "target_language": normalized_language,
        "violations": sorted(set(violations)),
        "applied_reason_codes": sorted(set(applied_reason_codes)),
    }
    return allow_recovery, policy_eval
