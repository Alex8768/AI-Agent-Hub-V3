"""LLM planner policy helpers extracted from answer service."""

from __future__ import annotations

import hashlib

_DEFAULT_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def parse_llm_planner_intent(
    raw_text: str,
    *,
    allowed_intents: tuple[str, ...] = _DEFAULT_ALLOWED_INTENTS,
) -> str:
    lowered = str(raw_text or "").strip().lower()
    for label in allowed_intents:
        if label in lowered:
            return label
    if lowered in {"project", "start project"} and "start_project" in set(allowed_intents):
        return "start_project"
    if lowered in {"meeting", "prepare meeting"} and "prepare_meeting" in set(allowed_intents):
        return "prepare_meeting"
    if lowered in {"chat", "general chat"} and "general_chat" in set(allowed_intents):
        return "general_chat"
    return ""


def build_deterministic_plan(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
    plan_contract_version: str,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": str(plan_contract_version or ""),
            "plan_id": "",
            "status": "disabled",
            "deterministic": True,
            "intent": "disabled",
            "steps": [],
            "requires_confirmation": False,
            "reason_codes": ["assistant_mode_disabled"],
        }

    intent = str(intent_payload.get("intent", "general_query") or "general_query")
    normalized_query = str(query or "").strip().lower()
    seed = f"{intent}|{normalized_query}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    plan_id = f"plan:{intent}:{digest}"
    steps: list[dict[str, object]]

    if intent == "start_project":
        steps = [
            {
                "step_id": "step:1",
                "role": "workspace_manager",
                "action": "prepare_project_workspace_draft",
                "parameters": {"template": "default_project"},
                "depends_on": [],
            },
            {
                "step_id": "step:2",
                "role": "planning_assistant",
                "action": "prepare_timeline_draft",
                "parameters": {"horizon_days": 30},
                "depends_on": ["step:1"],
            },
            {
                "step_id": "step:3",
                "role": "research_assistant",
                "action": "prepare_contacts_research_draft",
                "parameters": {"max_contacts": 5},
                "depends_on": [],
            },
        ]
    elif intent == "prepare_meeting":
        steps = [
            {
                "step_id": "step:1",
                "role": "meeting_assistant",
                "action": "prepare_agenda_draft",
                "parameters": {"sections": 4},
                "depends_on": [],
            },
            {
                "step_id": "step:2",
                "role": "context_assistant",
                "action": "prepare_context_summary_draft",
                "parameters": {"max_items": 8},
                "depends_on": [],
            },
        ]
    elif intent == "general_chat":
        steps = [
            {
                "step_id": "step:1",
                "role": "assistant",
                "action": "prepare_friendly_reply",
                "parameters": {},
                "depends_on": [],
            }
        ]
    else:
        steps = [
            {
                "step_id": "step:1",
                "role": "assistant",
                "action": "prepare_clarification_prompt",
                "parameters": {},
                "depends_on": [],
            }
        ]

    return {
        "contract_version": str(plan_contract_version or ""),
        "plan_id": plan_id,
        "status": "ready" if steps else "idle",
        "deterministic": True,
        "intent": intent,
        "steps": steps,
        "requires_confirmation": bool(steps),
        "reason_codes": ["deterministic_plan_built"],
    }


async def build_planner_with_fallback(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
    llm: object | None,
    llm_enabled: bool,
    llm_model: str,
    llm_error: str,
    deterministic_plan_builder: object,
    parse_intent_fn: object,
    llm_planner_contract_version: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    base_intent = dict(intent_payload or {})
    plan = deterministic_plan_builder(
        query=query,
        intent_payload=base_intent,
        assistant_mode_enabled=assistant_mode_enabled,
    )
    intent_name = str(base_intent.get("intent", "general_query") or "general_query")
    plan_id = str(plan.get("plan_id", "") or "")
    if not assistant_mode_enabled:
        return base_intent, plan, {
            "contract_version": str(llm_planner_contract_version or ""),
            "source": "heuristic",
            "status": "disabled",
            "model": str(llm_model or ""),
            "intent": intent_name,
            "plan_id": plan_id,
            "reason_codes": ["assistant_mode_disabled"],
        }
    if not llm_enabled:
        return base_intent, plan, {
            "contract_version": str(llm_planner_contract_version or ""),
            "source": "heuristic",
            "status": "disabled",
            "model": str(llm_model or ""),
            "intent": intent_name,
            "plan_id": plan_id,
            "reason_codes": ["llm_planner_disabled"],
        }
    if llm is None or not callable(getattr(llm, "generate", None)):
        reason_codes = ["llm_planner_adapter_unavailable"]
        if str(llm_error or "").strip():
            reason_codes.append("llm_planner_adapter_error")
        return base_intent, plan, {
            "contract_version": str(llm_planner_contract_version or ""),
            "source": "fallback",
            "status": "fallback",
            "model": str(llm_model or ""),
            "intent": intent_name,
            "plan_id": plan_id,
            "reason_codes": reason_codes,
        }

    prompt = (
        "Classify user request intent with one label only: "
        "start_project, prepare_meeting, general_chat, general_query.\n"
        f"User request: {str(query or '').strip()}\n"
        "Label:"
    )
    try:
        raw = await llm.generate(prompt)
        selected_intent = parse_intent_fn(str(raw or ""))
    except Exception:
        selected_intent = ""
    if not selected_intent:
        return base_intent, plan, {
            "contract_version": str(llm_planner_contract_version or ""),
            "source": "fallback",
            "status": "fallback",
            "model": str(llm_model or ""),
            "intent": intent_name,
            "plan_id": plan_id,
            "reason_codes": ["llm_planner_invalid_response_fallback"],
        }

    merged_intent = dict(base_intent)
    merged_intent["intent"] = selected_intent
    merged_intent["source"] = "llm"
    merged_intent["reason_codes"] = sorted(
        set(
            [str(x) for x in list(base_intent.get("reason_codes") or []) if str(x or "").strip()]
            + ["llm_planner_intent_selected"]
        )
    )
    llm_plan = deterministic_plan_builder(
        query=query,
        intent_payload=merged_intent,
        assistant_mode_enabled=assistant_mode_enabled,
    )
    return merged_intent, llm_plan, {
        "contract_version": str(llm_planner_contract_version or ""),
        "source": "llm",
        "status": "ready",
        "model": str(llm_model or ""),
        "intent": selected_intent,
        "plan_id": str(llm_plan.get("plan_id", "") or ""),
        "reason_codes": ["llm_planner_adapter_selected_intent"],
    }


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


def build_feedback_learning_bundle(
    *,
    req: object,
    assistant_mode_enabled: bool,
    feedback_contract_version: str,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": str(feedback_contract_version or ""),
            "mode": "approve_cancel_edit_feedback",
            "status": "disabled",
            "signals": [],
            "latest_signal": "none",
            "signal_counts": {"approve": 0, "cancel": 0, "edit": 0},
            "reason_codes": ["assistant_mode_disabled"],
        }

    filters = dict(getattr(req, "filters", {}) or {})
    allowed = {"approve", "cancel", "edit"}

    def _to_signal(raw: object) -> str:
        value = str(raw or "").strip().lower()
        return value if value in allowed else ""

    normalized_signals: list[str] = []
    for raw in list(filters.get("feedback_signals") or []):
        signal = _to_signal(raw)
        if signal:
            normalized_signals.append(signal)

    for row in list(filters.get("feedback_events") or []):
        event = dict(row or {})
        signal = _to_signal(event.get("signal", ""))
        if signal:
            normalized_signals.append(signal)

    explicit_signal = _to_signal(filters.get("feedback_signal", ""))
    if explicit_signal:
        normalized_signals.append(explicit_signal)

    decision_signal = _to_signal(filters.get("handshake_decision", ""))
    if decision_signal:
        normalized_signals.append(decision_signal)

    if bool(filters.get("feedback_edit_payload") or filters.get("handshake_edit_payload")):
        normalized_signals.append("edit")

    signals: list[str] = []
    seen: set[str] = set()
    for signal in normalized_signals:
        if signal in seen:
            continue
        seen.add(signal)
        signals.append(signal)

    latest = signals[-1] if signals else "none"
    counts = {
        "approve": int(1 if "approve" in signals else 0),
        "cancel": int(1 if "cancel" in signals else 0),
        "edit": int(1 if "edit" in signals else 0),
    }
    reasons = ["feedback_capture_adapter_normalized"]
    if latest != "none":
        reasons.append(f"feedback_signal_detected:{latest}")
    return {
        "contract_version": str(feedback_contract_version or ""),
        "mode": "approve_cancel_edit_feedback",
        "status": "ready",
        "signals": signals,
        "latest_signal": latest,
        "signal_counts": counts,
        "reason_codes": reasons,
    }


def build_feedback_adaptation_bundle(
    *,
    feedback_bundle: dict[str, object],
    intent_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    adaptation_contract_version: str,
    allowed_intents: tuple[str, ...] = _DEFAULT_ALLOWED_INTENTS,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": str(adaptation_contract_version or ""),
            "mode": "feedback_to_planning_adaptation",
            "status": "disabled",
            "source": "deterministic",
            "latest_signal": "none",
            "boosted_intents": [],
            "suppressed_intents": [],
            "reason_codes": ["assistant_mode_disabled"],
        }

    feedback = dict(feedback_bundle or {})
    intent = dict(intent_bundle or {})
    plan = dict(plan_bundle or {})
    latest = str(feedback.get("latest_signal", "none") or "none").strip().lower()
    if latest not in {"approve", "cancel", "edit"}:
        latest = "none"

    reason_codes = ["feedback_adaptation_contract_baseline_built"]
    status = "ready"
    current_intent = str(intent.get("intent", "") or plan.get("intent", "") or "general_query").strip()
    if not current_intent:
        current_intent = "general_query"
    if current_intent not in set(allowed_intents):
        current_intent = "general_query"

    boosted_intents: list[str] = []
    suppressed_intents: list[str] = []
    if latest == "none":
        status = "idle"
        reason_codes = ["feedback_adaptation_no_signal"]
    elif latest == "approve":
        boosted_intents = [current_intent]
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked", f"feedback_adaptation_boosted:{current_intent}"]
    elif latest == "cancel":
        boosted_intents = ["general_query"]
        if current_intent != "general_query":
            suppressed_intents = [current_intent]
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked", "feedback_adaptation_boosted:general_query"]
        if suppressed_intents:
            reason_codes.append(f"feedback_adaptation_suppressed:{suppressed_intents[0]}")
    elif latest == "edit":
        boosted_intents = [current_intent]
        if current_intent != "prepare_meeting":
            boosted_intents.append("prepare_meeting")
        reason_codes = ["feedback_adaptation_signal_to_plan_ranked"]
        reason_codes.extend([f"feedback_adaptation_boosted:{x}" for x in boosted_intents])

    return {
        "contract_version": str(adaptation_contract_version or ""),
        "mode": "feedback_to_planning_adaptation",
        "status": status,
        "source": "deterministic",
        "latest_signal": latest,
        "boosted_intents": boosted_intents,
        "suppressed_intents": suppressed_intents,
        "reason_codes": reason_codes,
    }


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


def build_tool_selection_bundle(
    *,
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    mcp_tools: list[dict[str, object]] | None,
    tool_selection_contract_version: str,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": str(tool_selection_contract_version or ""),
            "mode": "mcp_aware_selector",
            "status": "disabled",
            "source": "none",
            "selected_tools": [],
            "blocked_step_ids": [],
            "reason_codes": ["assistant_mode_disabled"],
        }

    plan = dict(plan_bundle or {})
    steps = [dict(step or {}) for step in list(plan.get("steps") or [])]
    if not steps:
        return {
            "contract_version": str(tool_selection_contract_version or ""),
            "mode": "mcp_aware_selector",
            "status": "idle",
            "source": "deterministic",
            "selected_tools": [],
            "blocked_step_ids": [],
            "reason_codes": ["tool_selection_no_plan_steps"],
        }

    def _tokens(value: object) -> set[str]:
        text = str(value or "").strip().lower()
        if not text:
            return set()
        normalized = "".join(ch if ch.isalnum() else " " for ch in text)
        return {tok for tok in normalized.split() if tok}

    tool_rows = [dict(row or {}) for row in list(mcp_tools or [])]
    tool_rows = [row for row in tool_rows if str(row.get("tool_name", "") or "").strip()]
    selected_tools: list[dict[str, object]] = []
    used_mcp = False
    for step in steps:
        step_id = str(step.get("step_id", "") or "")
        action = str(step.get("action", "") or "")
        role = str(step.get("role", "") or "")
        step_tokens = _tokens(f"{action} {role}")
        best_name = "none"
        best_score = 0
        for tool in tool_rows:
            tool_name = str(tool.get("tool_name", "") or "")
            haystack = " ".join(
                [
                    tool_name,
                    str(tool.get("description", "") or ""),
                    " ".join(str(x) for x in list(tool.get("tags") or [])),
                ]
            )
            score = len(step_tokens & _tokens(haystack))
            if score > best_score:
                best_score = score
                best_name = tool_name
        if best_score > 0 and best_name != "none":
            used_mcp = True
            selected_tools.append(
                {
                    "step_id": step_id,
                    "tool_name": best_name,
                    "route": "mcp_registry_match",
                    "reason": "tool_selection_mcp_match",
                }
            )
        else:
            selected_tools.append(
                {
                    "step_id": step_id,
                    "tool_name": "none",
                    "route": "deterministic_fallback",
                    "reason": "tool_selection_fallback_no_match",
                }
            )
    source = "mcp" if used_mcp else "deterministic"
    reasons = ["tool_selection_adapter_applied"] + (
        ["tool_selection_mcp_matched"] if used_mcp else ["tool_selection_fallback_used"]
    )
    return {
        "contract_version": str(tool_selection_contract_version or ""),
        "mode": "mcp_aware_selector",
        "status": "ready",
        "source": source,
        "selected_tools": selected_tools,
        "blocked_step_ids": [],
        "reason_codes": reasons,
    }


def bridge_plan_to_draft_actions(
    *,
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    language: str,
    actions_enabled: bool,
) -> dict[str, object]:
    if not actions_enabled:
        return dict(draft_actions_bundle or {})

    current = dict(draft_actions_bundle or {})
    existing_actions = list(current.get("actions") or [])
    if existing_actions:
        return current

    steps = [dict(step or {}) for step in list(plan_bundle.get("steps") or [])]
    if not steps:
        return current

    plan_id = str(plan_bundle.get("plan_id", "") or "")
    bridged_actions: list[dict[str, object]] = []
    for idx, step in enumerate(steps, start=1):
        step_id = str(step.get("step_id", "") or f"step:{idx}")
        step_action = str(step.get("action", "prepare_step_draft") or "prepare_step_draft")
        step_role = str(step.get("role", "assistant") or "assistant")
        if language == "ru":
            summary = f"Черновик шага плана: {step_action} ({step_role})."
            rollback = "Откат не требуется: создан только черновик шага."
        else:
            summary = f"Draft plan step prepared: {step_action} ({step_role})."
            rollback = "No rollback required: draft-only plan step."
        bridged_actions.append(
            {
                "action_id": f"draft_action:{plan_id}:{step_id}" if plan_id else f"draft_action:{step_id}",
                "action_type": "prepare_plan_step_draft",
                "status": "draft",
                "requires_confirmation": True,
                "estimated_impact": "low",
                "parameters": {
                    "plan_id": plan_id,
                    "step_id": step_id,
                    "role": step_role,
                    "action": step_action,
                },
                "preview": {
                    "title": step_action,
                    "summary": summary,
                    "rank": idx,
                },
                "rollback_plan": rollback,
            }
        )

    reason_codes = sorted(
        set([str(x) for x in list(current.get("reason_codes") or []) if str(x or "").strip()])
        | {"draft_actions_from_plan_bridge"}
    )
    return {
        "status": "ready",
        "actions": bridged_actions,
        "top_action_id": str((bridged_actions[0] or {}).get("action_id", "") or ""),
        "requires_confirmation": bool(bridged_actions),
        "reason_codes": reason_codes,
        "warnings": list(current.get("warnings") or []),
    }


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
