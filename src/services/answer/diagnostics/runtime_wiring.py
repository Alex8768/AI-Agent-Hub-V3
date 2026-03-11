"""Runtime diagnostics wiring helpers extracted from answer service."""

from __future__ import annotations

from src.services.answer.response.language import normalize_language_tag

_DEFAULT_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def _default_assistant_recovery_policy_contract() -> dict[str, object]:
    return {
        "mode": "assistant_chat_recovery_guarded",
        "allow_low_evidence_only": True,
        "allowed_intents": ["general_chat", "general_query"],
        "block_greeting_queries": True,
        "allowed_languages": ["ru", "en"],
        "require_assistant_mode": True,
        "fallback_on_policy_violation": True,
    }


def wire_planner_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    intent = dict(diag.get("assistant_intent") or {})
    plan = dict(diag.get("assistant_plan") or {})
    llm_planner = dict(diag.get("assistant_llm_planner") or {})
    llm_planner_policy = dict(diag.get("llm_planner_policy") or {})

    plan_id = str(plan.get("plan_id", "") or "")
    plan_intent = str(plan.get("intent", "") or "")
    intent_name = str(intent.get("intent", plan_intent or "general_query") or "general_query")
    if not plan_intent:
        plan["intent"] = intent_name
    if not llm_planner.get("intent"):
        llm_planner["intent"] = intent_name

    reason_codes = [str(x) for x in list(llm_planner.get("reason_codes") or []) if str(x or "").strip()]
    if str(llm_planner.get("plan_id", "") or "") != plan_id:
        llm_planner["plan_id"] = plan_id
        reason_codes.append("llm_planner_runtime_plan_id_synced")
    llm_planner["reason_codes"] = sorted(set(reason_codes))

    llm_policy_reasons = [str(x) for x in list(llm_planner_policy.get("applied_reason_codes") or []) if str(x or "").strip()]
    if "llm_planner_runtime_wired" not in llm_policy_reasons:
        llm_policy_reasons.append("llm_planner_runtime_wired")
    llm_planner_policy["applied_reason_codes"] = sorted(set(llm_policy_reasons))
    llm_planner_policy.setdefault("violations", [])

    diag["assistant_plan"] = plan
    diag["assistant_llm_planner"] = llm_planner
    diag["llm_planner_policy"] = llm_planner_policy
    return diag


def wire_tool_selection_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    plan = dict(diag.get("assistant_plan") or {})
    tool_selection = dict(diag.get("assistant_tool_selection") or {})
    tool_selection_policy = dict(diag.get("tool_selection_policy") or {})

    steps = [dict(x or {}) for x in list(plan.get("steps") or [])]
    plan_step_ids = [str(x.get("step_id", "") or "") for x in steps if str(x.get("step_id", "") or "")]
    plan_step_id_set = set(plan_step_ids)
    selected_rows = [dict(x or {}) for x in list(tool_selection.get("selected_tools") or [])]
    blocked_step_ids = [str(x) for x in list(tool_selection.get("blocked_step_ids") or []) if str(x)]
    reason_codes = [str(x) for x in list(tool_selection.get("reason_codes") or []) if str(x or "").strip()]
    policy_reasons = [str(x) for x in list(tool_selection_policy.get("applied_reason_codes") or []) if str(x or "").strip()]
    policy_violations = [str(x) for x in list(tool_selection_policy.get("violations") or []) if str(x or "").strip()]

    by_step: dict[str, dict[str, object]] = {}
    orphaned_step_ids: list[str] = []
    for row in selected_rows:
        step_id = str(row.get("step_id", "") or "")
        if not step_id:
            continue
        if plan_step_id_set and step_id not in plan_step_id_set:
            orphaned_step_ids.append(step_id)
            blocked_step_ids.append(step_id)
            continue
        if step_id not in by_step:
            by_step[step_id] = row

    if orphaned_step_ids:
        reason_codes.append("tool_selection_runtime_orphaned_steps_removed")
        policy_violations.append("tool_selection_runtime_orphaned_step_removed")

    wired_rows: list[dict[str, object]] = []
    for step_id in plan_step_ids:
        row = by_step.get(step_id)
        if row is None:
            row = {
                "step_id": step_id,
                "tool_name": "none",
                "route": "deterministic_fallback",
                "reason": "tool_selection_runtime_step_backfilled",
            }
            reason_codes.append("tool_selection_runtime_backfilled")
        wired_rows.append(row)

    if "tool_selection_runtime_wired" not in reason_codes:
        reason_codes.append("tool_selection_runtime_wired")
    if "tool_selection_runtime_wired" not in policy_reasons:
        policy_reasons.append("tool_selection_runtime_wired")

    tool_selection["selected_tools"] = wired_rows
    tool_selection["blocked_step_ids"] = sorted(set(blocked_step_ids))
    tool_selection["reason_codes"] = sorted(set(reason_codes))
    tool_selection_policy["applied_reason_codes"] = sorted(set(policy_reasons))
    tool_selection_policy["violations"] = sorted(set(policy_violations))

    diag["assistant_tool_selection"] = tool_selection
    diag["tool_selection_policy"] = tool_selection_policy
    return diag


def wire_feedback_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    feedback = dict(diag.get("assistant_feedback_learning") or {})
    feedback_policy = dict(diag.get("feedback_policy") or {})

    allowed = {"approve", "cancel", "edit"}
    raw_signals = [str(x).strip().lower() for x in list(feedback.get("signals") or []) if str(x).strip()]
    signals: list[str] = []
    seen: set[str] = set()
    dropped_unknown = False
    for signal in raw_signals:
        if signal not in allowed:
            dropped_unknown = True
            continue
        if signal in seen:
            continue
        seen.add(signal)
        signals.append(signal)

    latest = str(feedback.get("latest_signal", "none") or "none").strip().lower()
    if latest not in allowed:
        latest = "none"
    if latest != "none" and latest not in signals:
        signals.append(latest)
    if latest == "none" and signals:
        latest = signals[-1]

    counts = {
        "approve": int(1 if "approve" in signals else 0),
        "cancel": int(1 if "cancel" in signals else 0),
        "edit": int(1 if "edit" in signals else 0),
    }

    reason_codes = [str(x) for x in list(feedback.get("reason_codes") or []) if str(x or "").strip()]
    if dropped_unknown:
        reason_codes.append("feedback_runtime_unknown_signals_removed")
    if "feedback_runtime_wired" not in reason_codes:
        reason_codes.append("feedback_runtime_wired")

    policy_reasons = [str(x) for x in list(feedback_policy.get("applied_reason_codes") or []) if str(x or "").strip()]
    if "feedback_runtime_wired" not in policy_reasons:
        policy_reasons.append("feedback_runtime_wired")
    feedback_policy.setdefault("violations", [])
    feedback_policy["applied_reason_codes"] = sorted(set(policy_reasons))

    feedback["signals"] = signals
    feedback["latest_signal"] = latest
    feedback["signal_counts"] = counts
    feedback["reason_codes"] = sorted(set(reason_codes))

    diag["assistant_feedback_learning"] = feedback
    diag["feedback_policy"] = feedback_policy
    return diag


def wire_feedback_adaptation_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
    allowed_intents: tuple[str, ...] = _DEFAULT_ALLOWED_INTENTS,
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    plan = dict(diag.get("assistant_plan") or {})
    feedback = dict(diag.get("assistant_feedback_learning") or {})
    adaptation = dict(diag.get("assistant_feedback_adaptation") or {})
    adaptation_policy = dict(diag.get("adaptation_policy") or {})

    allowed_signals = {"none", "approve", "cancel", "edit"}
    allowed_intent_set = set(allowed_intents)
    latest = str(adaptation.get("latest_signal", "none") or "none").strip().lower()
    feedback_latest = str(feedback.get("latest_signal", "none") or "none").strip().lower()
    current_intent = str(plan.get("intent", "") or "general_query").strip() or "general_query"
    if current_intent not in allowed_intent_set:
        current_intent = "general_query"

    boosted_raw = [str(x).strip() for x in list(adaptation.get("boosted_intents") or []) if str(x).strip()]
    suppressed_raw = [str(x).strip() for x in list(adaptation.get("suppressed_intents") or []) if str(x).strip()]
    boosted: list[str] = []
    suppressed: list[str] = []
    seen_b: set[str] = set()
    seen_s: set[str] = set()
    dropped_unknown = False
    removed_overlap = False
    backfilled = False

    if latest not in allowed_signals:
        latest = "none"
        dropped_unknown = True
    if feedback_latest in allowed_signals and feedback_latest != latest:
        latest = feedback_latest

    for intent in boosted_raw:
        if intent not in allowed_intent_set:
            dropped_unknown = True
            continue
        if intent in seen_b:
            continue
        seen_b.add(intent)
        boosted.append(intent)

    for intent in suppressed_raw:
        if intent not in allowed_intent_set:
            dropped_unknown = True
            continue
        if intent in seen_s:
            continue
        seen_s.add(intent)
        suppressed.append(intent)

    if latest in {"approve", "edit"} and not boosted:
        boosted = [current_intent]
        backfilled = True
    if latest == "cancel" and not boosted:
        boosted = ["general_query"]
        backfilled = True
    if latest == "none":
        suppressed = []

    overlap = set(boosted) & set(suppressed)
    if overlap:
        suppressed = [intent for intent in suppressed if intent not in overlap]
        removed_overlap = True

    max_boosted = int(adaptation_policy.get("max_boosted_intents", 2) or 2)
    max_suppressed = int(adaptation_policy.get("max_suppressed_intents", 1) or 1)
    if len(boosted) > max_boosted:
        boosted = boosted[:max_boosted]
    if len(suppressed) > max_suppressed:
        suppressed = suppressed[:max_suppressed]

    reason_codes = [str(x) for x in list(adaptation.get("reason_codes") or []) if str(x or "").strip()]
    reason_codes.append("feedback_adaptation_runtime_wired")
    if backfilled:
        reason_codes.append("feedback_adaptation_runtime_backfilled")
    if dropped_unknown:
        reason_codes.append("feedback_adaptation_runtime_unknown_intent_removed")
    if removed_overlap:
        reason_codes.append("feedback_adaptation_runtime_overlap_removed")

    policy_reasons = [str(x) for x in list(adaptation_policy.get("applied_reason_codes") or []) if str(x or "").strip()]
    policy_reasons.append("feedback_adaptation_runtime_wired")
    policy_violations = [str(x) for x in list(adaptation_policy.get("violations") or []) if str(x or "").strip()]
    if removed_overlap:
        policy_violations.append("feedback_adaptation_runtime_overlap_removed")
    if dropped_unknown:
        policy_violations.append("feedback_adaptation_runtime_unknown_intent_removed")

    adaptation["latest_signal"] = latest
    adaptation["boosted_intents"] = boosted
    adaptation["suppressed_intents"] = suppressed
    adaptation["reason_codes"] = sorted(set(reason_codes))
    adaptation_policy["applied_reason_codes"] = sorted(set(policy_reasons))
    adaptation_policy["violations"] = sorted(set(policy_violations))

    diag["assistant_feedback_adaptation"] = adaptation
    diag["adaptation_policy"] = adaptation_policy
    return diag


def wire_assistant_recovery_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = dict(diagnostics or {})
    response_language = str(diag.get("response_language", "auto") or "auto")
    query_text = str(diag.get("query", "") or "")
    target_language = normalize_language_tag(response_language, query=query_text)

    policy = dict(diag.get("assistant_recovery_policy") or _default_assistant_recovery_policy_contract())
    policy.setdefault("mode", "assistant_chat_recovery_guarded")
    policy["allow_low_evidence_only"] = bool(policy.get("allow_low_evidence_only", True))
    policy["block_greeting_queries"] = bool(policy.get("block_greeting_queries", True))
    policy["require_assistant_mode"] = bool(policy.get("require_assistant_mode", True))
    policy["fallback_on_policy_violation"] = bool(policy.get("fallback_on_policy_violation", True))
    policy["allowed_intents"] = [
        intent
        for intent in [str(x).strip() for x in list(policy.get("allowed_intents") or []) if str(x or "").strip()]
        if intent in {"general_chat", "general_query"}
    ] or ["general_chat", "general_query"]
    policy["allowed_languages"] = [
        language
        for language in [str(x).strip().lower() for x in list(policy.get("allowed_languages") or []) if str(x or "").strip()]
        if language in {"ru", "en"}
    ] or ["ru", "en"]
    policy["target_language"] = target_language

    known_violations = {
        "assistant_chat_recovery_assistant_mode_disabled",
        "assistant_chat_recovery_requires_low_evidence",
        "assistant_chat_recovery_intent_not_allowlisted",
        "assistant_chat_recovery_greeting_blocked",
        "assistant_chat_recovery_language_not_allowlisted",
    }
    raw_violations = [str(x).strip() for x in list(policy.get("violations") or []) if str(x or "").strip()]
    violations = [code for code in raw_violations if code in known_violations]
    policy_reasons = [str(x) for x in list(policy.get("applied_reason_codes") or []) if str(x or "").strip()]

    if len(violations) != len(raw_violations):
        policy_reasons.append("assistant_chat_recovery_runtime_unknown_violation_removed")
    if violations and "assistant_chat_recovery_policy_forced_fallback" not in policy_reasons:
        policy_reasons.append("assistant_chat_recovery_policy_forced_fallback")
    policy_reasons.append("assistant_chat_recovery_runtime_wired")

    recovery_applied = bool(diag.get("assistant_chat_recovery_applied", False))
    if recovery_applied and violations:
        diag["assistant_chat_recovery_applied"] = False
        policy_reasons.append("assistant_chat_recovery_runtime_applied_flag_reset")

    planning_reasons = [str(x) for x in list(diag.get("planning_reason_codes") or []) if str(x or "").strip()]
    planning_reasons.extend(policy_reasons)
    if bool(diag.get("assistant_chat_recovery_applied", False)):
        planning_reasons.append("assistant_chat_recovery_applied")
    diag["planning_reason_codes"] = sorted(set(planning_reasons))

    policy["violations"] = sorted(set(violations))
    policy["applied_reason_codes"] = sorted(set(policy_reasons))
    diag["assistant_recovery_policy"] = policy
    return diag


def wire_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = wire_planner_runtime_diagnostics(diagnostics=diagnostics)
    diag = wire_tool_selection_runtime_diagnostics(diagnostics=diag)
    diag = wire_feedback_runtime_diagnostics(diagnostics=diag)
    diag = wire_feedback_adaptation_runtime_diagnostics(diagnostics=diag)
    diag = wire_assistant_recovery_runtime_diagnostics(diagnostics=diag)
    return diag
