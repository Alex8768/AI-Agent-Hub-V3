from __future__ import annotations

import hashlib
import json
import time
from time import perf_counter
from typing import Any

from fastapi import Request

from src.layers.pro.anticipatory import (
    OpportunityScanner,
    WhisperRunner,
    build_proactive_suggestion_bundle,
)
from src.layers.pro.reasoning.control.execution_policy import build_reasoning_execution_policy
from src.layers.pro.reasoning.contracts import (
    APPROVAL_SESSION_CONTRACT_VERSION,
    ADAPTATION_CONTRACT_VERSION,
    AnswerRequest,
    DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
    EVIDENCE_CONTRACT_VERSION,
    EXECUTION_PILOT_CONTRACT_VERSION,
    EXECUTION_RECEIPT_CONTRACT_VERSION,
    FEEDBACK_CONTRACT_VERSION,
    HANDSHAKE_CONTRACT_VERSION,
    IDEMPOTENCY_RECORD_CONTRACT_VERSION,
    INTENT_CONTRACT_VERSION,
    LLM_PLANNER_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
    TOOL_SELECTION_CONTRACT_VERSION,
    SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN,
    SELF_CHECK_MISSING_MINIMAL_COUNT_MAX,
    VERIFY_DIAGNOSTICS_VERSION,
    VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED,
    VERIFY_SELF_CHECK_REASONS_COUNT_MAX,
    VERIFY_SELF_CHECK_STATUS_REQUIRED,
)
from src.observability.request_context import get_request_id

SESSION_MEMORY_MAX_CHARS = 4000
EXECUTION_IDEMPOTENCY_CONTRACT_VERSION = "v1"
EXECUTION_GATEWAY_CONTRACT_VERSION = "v1"
EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES: tuple[str, ...] = (
    "prepare_summary_draft",
    "collect_context_draft",
    "prepare_workflow_draft",
)
EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN = "prepare_*_draft"
EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS = 1
_EXECUTION_IDEMPOTENCY_SEEN: dict[str, str] = {}
_LLM_PLANNER_ALLOWED_INTENTS: tuple[str, ...] = (
    "start_project",
    "prepare_meeting",
    "general_chat",
    "general_query",
)


def _clip_text(value: object, *, max_chars: int = SESSION_MEMORY_MAX_CHARS) -> str:
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _durable_approval_record_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:durable:approval_session_record"


def _durable_idempotency_record_key(*, session_id: str, idempotency_key: str = "") -> str:
    sid = str(session_id or "default")
    ikey = str(idempotency_key or "").strip()
    if ikey:
        return f"session:{sid}:durable:idempotency_record:{ikey}"
    return f"session:{sid}:durable:idempotency_record:last"


def _detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"


def _is_allowlisted_pilot_action_type(action_type: str, allowlisted_action_types: set[str]) -> bool:
    normalized = str(action_type or "").strip()
    if not normalized:
        return False
    if normalized in allowlisted_action_types:
        return True
    return normalized.startswith("prepare_") and normalized.endswith("_draft")


def _build_assistant_fallback_answer(*, query: str, language: str) -> str:
    if language == "ru":
        return (
            "Привет! Я готов помочь как ассистент по рабочим задачам. "
            "Могу подготовить план, черновики и следующие шаги по вашему запросу. "
            "Если хотите точный ответ по внутренним данным, загрузите документы или уточните контекст."
        )
    return (
        "Hi! I can help as an operations assistant. "
        "I can prepare a plan, drafts, and next steps for your request. "
        "If you need a source-grounded answer from internal data, upload documents or provide more context."
    )


def _rank_proactive_bundle(bundle: dict[str, object]) -> dict[str, object]:
    suggestions = [dict(row or {}) for row in list(bundle.get("suggestions") or [])]
    normalized: list[dict[str, object]] = []
    for row in suggestions:
        try:
            confidence = float(row.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        priority = int(round(confidence * 100))
        normalized.append(
            {
                **row,
                "priority": priority,
            }
        )

    normalized.sort(
        key=lambda x: (
            -int(x.get("priority", 0) or 0),
            str(x.get("suggestion_type", "") or ""),
            str(x.get("suggestion_id", "") or ""),
        )
    )
    ranked: list[dict[str, object]] = []
    for idx, row in enumerate(normalized, start=1):
        ranked.append(
            {
                **row,
                "rank": idx,
            }
        )

    reason_codes = sorted(
        set(
            [
                str(x)
                for x in list(bundle.get("reason_codes") or [])
                if str(x or "").strip()
            ]
            + (["ranked_by_priority"] if ranked else [])
        )
    )
    top_suggestion_id = str((ranked[0] or {}).get("suggestion_id", "") or "") if ranked else ""
    status = "active" if ranked else str(bundle.get("status", "idle") or "idle")
    return {
        "status": status,
        "suggestions": ranked,
        "top_suggestion_id": top_suggestion_id,
        "reason_codes": reason_codes,
        "warnings": list(bundle.get("warnings") or []),
    }


def _build_draft_action_bundle(
    *,
    proactive_bundle: dict[str, object],
    language: str,
    actions_enabled: bool,
) -> dict[str, object]:
    rows = [dict(row or {}) for row in list(proactive_bundle.get("suggestions") or [])]
    if not actions_enabled:
        return {
            "status": "disabled",
            "actions": [],
            "top_action_id": "",
            "requires_confirmation": False,
            "reason_codes": ["assistant_actions_disabled"],
            "warnings": [],
        }

    def _map_action_type(suggestion_type: str) -> str:
        key = str(suggestion_type or "").strip().lower()
        if key == "automation":
            return "prepare_workflow_draft"
        if key == "summarization":
            return "prepare_summary_draft"
        if key == "retrieval":
            return "collect_context_draft"
        return "prepare_follow_up_draft"

    actions: list[dict[str, object]] = []
    for idx, row in enumerate(rows, start=1):
        sid = str(row.get("suggestion_id", "") or f"suggestion:{idx}")
        rank = int(row.get("rank", idx) or idx)
        action_id = f"draft_action:{sid}"
        action_type = _map_action_type(str(row.get("suggestion_type", "") or ""))
        rationale = str(row.get("rationale", "") or "")
        if language == "ru":
            summary = rationale or "Подготовлен безопасный черновик действия для ревью."
            rollback = "Откат не требуется: действие черновое и не имеет side effects."
        else:
            summary = rationale or "Prepared a safe draft action for review."
            rollback = "No rollback required: draft action has no side effects."
        actions.append(
            {
                "action_id": action_id,
                "action_type": action_type,
                "status": "draft",
                "requires_confirmation": True,
                "estimated_impact": "low",
                "parameters": {
                    "source_suggestion_id": sid,
                    "priority": int(row.get("priority", 0) or 0),
                },
                "preview": {
                    "title": str(row.get("action_hint", "") or action_type),
                    "summary": summary,
                    "rank": rank,
                },
                "rollback_plan": rollback,
            }
        )

    top_action_id = str((actions[0] or {}).get("action_id", "") or "") if actions else ""
    return {
        "status": "ready" if actions else "idle",
        "actions": actions,
        "top_action_id": top_action_id,
        "requires_confirmation": bool(actions),
        "reason_codes": ["draft_actions_available"] if actions else ["no_suggestions_for_actions"],
        "warnings": [],
    }


def _infer_assistant_intent(*, query: str, assistant_mode_enabled: bool) -> dict[str, object]:
    text = str(query or "").strip()
    lowered = text.lower()

    if not assistant_mode_enabled:
        return {
            "intent": "disabled",
            "confidence": 0.0,
            "entities": {},
            "implicit_tasks": [],
            "source": "heuristic",
            "reason_codes": ["assistant_mode_disabled"],
        }

    if "проект" in lowered or "project" in lowered:
        return {
            "intent": "start_project",
            "confidence": 0.8,
            "entities": {"project_name": text[:120]},
            "implicit_tasks": [
                "project_workspace",
                "timeline_alignment",
                "contacts_research",
            ],
            "source": "heuristic",
            "reason_codes": ["keyword_project"],
        }
    if "встреч" in lowered or "митинг" in lowered or "meeting" in lowered:
        return {
            "intent": "prepare_meeting",
            "confidence": 0.7,
            "entities": {},
            "implicit_tasks": ["agenda_draft", "context_summary", "follow_up_tasks"],
            "source": "heuristic",
            "reason_codes": ["keyword_meeting"],
        }
    if "привет" in lowered or lowered.startswith("hi") or "hello" in lowered:
        return {
            "intent": "general_chat",
            "confidence": 0.6,
            "entities": {},
            "implicit_tasks": ["friendly_response"],
            "source": "heuristic",
            "reason_codes": ["keyword_greeting"],
        }
    return {
        "intent": "general_query",
        "confidence": 0.4,
        "entities": {},
        "implicit_tasks": [],
        "source": "heuristic",
        "reason_codes": ["fallback_general_query"],
    }


def _build_deterministic_plan(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": PLAN_CONTRACT_VERSION,
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
        "contract_version": PLAN_CONTRACT_VERSION,
        "plan_id": plan_id,
        "status": "ready" if steps else "idle",
        "deterministic": True,
        "intent": intent,
        "steps": steps,
        "requires_confirmation": bool(steps),
        "reason_codes": ["deterministic_plan_built"],
    }


def _parse_llm_planner_intent(raw_text: str) -> str:
    lowered = str(raw_text or "").strip().lower()
    for label in _LLM_PLANNER_ALLOWED_INTENTS:
        if label in lowered:
            return label
    if lowered in {"project", "start project"}:
        return "start_project"
    if lowered in {"meeting", "prepare meeting"}:
        return "prepare_meeting"
    if lowered in {"chat", "general chat"}:
        return "general_chat"
    return ""


async def _build_planner_with_fallback(
    *,
    query: str,
    intent_payload: dict[str, object],
    assistant_mode_enabled: bool,
    llm: object | None,
    llm_enabled: bool,
    llm_model: str,
    llm_error: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    base_intent = dict(intent_payload or {})
    plan = _build_deterministic_plan(
        query=query,
        intent_payload=base_intent,
        assistant_mode_enabled=assistant_mode_enabled,
    )
    intent_name = str(base_intent.get("intent", "general_query") or "general_query")
    plan_id = str(plan.get("plan_id", "") or "")
    if not assistant_mode_enabled:
        return base_intent, plan, {
            "contract_version": LLM_PLANNER_CONTRACT_VERSION,
            "source": "heuristic",
            "status": "disabled",
            "model": str(llm_model or ""),
            "intent": intent_name,
            "plan_id": plan_id,
            "reason_codes": ["assistant_mode_disabled"],
        }
    if not llm_enabled:
        return base_intent, plan, {
            "contract_version": LLM_PLANNER_CONTRACT_VERSION,
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
            "contract_version": LLM_PLANNER_CONTRACT_VERSION,
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
        selected_intent = _parse_llm_planner_intent(str(raw or ""))
    except Exception:
        selected_intent = ""
    if not selected_intent:
        return base_intent, plan, {
            "contract_version": LLM_PLANNER_CONTRACT_VERSION,
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
    llm_plan = _build_deterministic_plan(
        query=query,
        intent_payload=merged_intent,
        assistant_mode_enabled=assistant_mode_enabled,
    )
    return merged_intent, llm_plan, {
        "contract_version": LLM_PLANNER_CONTRACT_VERSION,
        "source": "llm",
        "status": "ready",
        "model": str(llm_model or ""),
        "intent": selected_intent,
        "plan_id": str(llm_plan.get("plan_id", "") or ""),
        "reason_codes": ["llm_planner_adapter_selected_intent"],
    }


def _build_llm_planner_policy_contract() -> dict[str, object]:
    return {
        "mode": "llm_planner_guarded",
        "allow_llm_source": True,
        "allowed_intents": list(_LLM_PLANNER_ALLOWED_INTENTS),
        "require_plan_id_prefix_match": True,
        "fallback_on_policy_violation": True,
    }


def _apply_llm_planner_policy_guards(
    *,
    intent_payload: dict[str, object],
    plan_bundle: dict[str, object],
    llm_planner_bundle: dict[str, object],
    policy_contract: dict[str, object],
    query: str,
    assistant_mode_enabled: bool,
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
            set([str(x) for x in list(fallback_intent.get("reason_codes") or []) if str(x or "").strip()] + ["llm_planner_policy_forced_fallback"])
        )
        fallback_plan = _build_deterministic_plan(
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


def _wire_planner_runtime_diagnostics(
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


def _wire_tool_selection_runtime_diagnostics(
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
    policy_reasons = [
        str(x) for x in list(tool_selection_policy.get("applied_reason_codes") or []) if str(x or "").strip()
    ]
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


def _wire_feedback_runtime_diagnostics(
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


def _wire_runtime_diagnostics(
    *,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    diag = _wire_planner_runtime_diagnostics(diagnostics=diagnostics)
    diag = _wire_tool_selection_runtime_diagnostics(diagnostics=diag)
    diag = _wire_feedback_runtime_diagnostics(diagnostics=diag)
    return diag


def _build_feedback_learning_bundle(
    *,
    req: AnswerRequest,
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": FEEDBACK_CONTRACT_VERSION,
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

    # Deterministic normalization: preserve first occurrence order, drop unknown/duplicates.
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
        "contract_version": FEEDBACK_CONTRACT_VERSION,
        "mode": "approve_cancel_edit_feedback",
        "status": "ready",
        "signals": signals,
        "latest_signal": latest,
        "signal_counts": counts,
        "reason_codes": reasons,
    }


def _build_feedback_policy_contract() -> dict[str, object]:
    return {
        "mode": "feedback_learning_guarded",
        "allowed_signals": ["approve", "cancel", "edit"],
        "max_signals_per_request": 3,
        "require_latest_in_signals": True,
        "fallback_on_policy_violation": True,
    }


def _apply_feedback_policy_guards(
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


def _build_feedback_adaptation_bundle(
    *,
    feedback_bundle: dict[str, object],
    intent_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": ADAPTATION_CONTRACT_VERSION,
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
    if current_intent not in _LLM_PLANNER_ALLOWED_INTENTS:
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
        "contract_version": ADAPTATION_CONTRACT_VERSION,
        "mode": "feedback_to_planning_adaptation",
        "status": status,
        "source": "deterministic",
        "latest_signal": latest,
        "boosted_intents": boosted_intents,
        "suppressed_intents": suppressed_intents,
        "reason_codes": reason_codes,
    }


def _build_feedback_adaptation_policy_contract() -> dict[str, object]:
    return {
        "mode": "feedback_adaptation_guarded",
        "allowed_latest_signals": ["none", "approve", "cancel", "edit"],
        "allowed_intents": list(_LLM_PLANNER_ALLOWED_INTENTS),
        "max_boosted_intents": 2,
        "max_suppressed_intents": 1,
        "forbid_boost_suppress_overlap": True,
        "fallback_on_policy_violation": True,
    }


def _apply_feedback_adaptation_policy_guards(
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


def _build_tool_selection_bundle(
    *,
    plan_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    mcp_tools: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": TOOL_SELECTION_CONTRACT_VERSION,
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
            "contract_version": TOOL_SELECTION_CONTRACT_VERSION,
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
    reasons = ["tool_selection_adapter_applied"] + (["tool_selection_mcp_matched"] if used_mcp else ["tool_selection_fallback_used"])
    return {
        "contract_version": TOOL_SELECTION_CONTRACT_VERSION,
        "mode": "mcp_aware_selector",
        "status": "ready",
        "source": source,
        "selected_tools": selected_tools,
        "blocked_step_ids": [],
        "reason_codes": reasons,
    }


def _build_tool_selection_policy_contract() -> dict[str, object]:
    return {
        "mode": "tool_selection_guarded",
        "allow_mcp_source": True,
        "allow_deterministic_fallback": True,
        "allowed_routes": ["mcp_registry_match", "deterministic_fallback", "diagnostics_only"],
        "require_plan_step_binding": True,
        "max_selected_tools": 5,
        "fallback_on_policy_violation": True,
    }


def _apply_tool_selection_policy_guards(
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


def _load_mcp_tools_from_runtime(http: Request) -> list[dict[str, object]]:
    state = getattr(getattr(http, "app", None), "state", None)
    registry = getattr(state, "mcp_registry", None) if state is not None else None
    if registry is None:
        return []
    try:
        list_tools = getattr(registry, "list_tools", None)
        if not callable(list_tools):
            return []
        rows = list(list_tools(enabled_only=True) or [])
        return [dict(row or {}) for row in rows]
    except Exception:
        return []


def _bridge_plan_to_draft_actions(
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


def _apply_plan_policy_guards(
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
        # Review-only policy: allow draft preparation actions only.
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


def _build_execution_handshake_bundle(
    *,
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    assistant_mode_enabled: bool,
    actions_enabled: bool,
) -> dict[str, object]:
    if not assistant_mode_enabled:
        return {
            "contract_version": HANDSHAKE_CONTRACT_VERSION,
            "state": "idle",
            "requires_confirmation": False,
            "confirmation_token": "",
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "receipt_id": "",
            "reason_codes": ["assistant_mode_disabled"],
        }
    if not actions_enabled:
        return {
            "contract_version": HANDSHAKE_CONTRACT_VERSION,
            "state": "idle",
            "requires_confirmation": False,
            "confirmation_token": "",
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "receipt_id": "",
            "reason_codes": ["assistant_actions_disabled"],
        }

    actions = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    if not actions:
        return {
            "contract_version": HANDSHAKE_CONTRACT_VERSION,
            "state": "idle",
            "requires_confirmation": False,
            "confirmation_token": "",
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "receipt_id": "",
            "reason_codes": ["no_draft_actions_available"],
        }
    plan_id = str(plan_bundle.get("plan_id", "") or "")
    seed = f"{plan_id}|{len(actions)}"
    token = f"confirm:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
    return {
        "contract_version": HANDSHAKE_CONTRACT_VERSION,
        "state": "pending_confirmation",
        "requires_confirmation": True,
        "confirmation_token": token,
        "approved_action_ids": [],
        "blocked_action_ids": [],
        "receipt_id": "",
        "reason_codes": ["awaiting_user_confirmation"],
    }


def _extract_handshake_transition_input(req: AnswerRequest) -> dict[str, object]:
    filters = dict(getattr(req, "filters", {}) or {})
    decision_raw = str(filters.get("handshake_decision", "") or "").strip().lower()
    if decision_raw not in {"approve", "cancel"}:
        decision_raw = ""

    token = str(filters.get("handshake_confirmation_token", "") or "").strip()
    requested_action_ids_raw = list(filters.get("handshake_action_ids") or [])
    requested_action_ids = [str(x).strip() for x in requested_action_ids_raw if str(x or "").strip()]
    idempotency_key = str(filters.get("handshake_idempotency_key", "") or "").strip()
    return {
        "decision": decision_raw,
        "confirmation_token": token,
        "requested_action_ids": requested_action_ids,
        "idempotency_key": idempotency_key,
    }


def _apply_handshake_transition(
    *,
    handshake_bundle: dict[str, object],
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> dict[str, object]:
    decision = str(transition_input.get("decision", "") or "")
    provided_token = str(transition_input.get("confirmation_token", "") or "")
    requested_raw = transition_input.get("requested_action_ids", None)
    requested_action_ids = [str(x) for x in list(requested_raw or []) if str(x)]
    if not decision:
        return dict(handshake_bundle or {})

    current = dict(handshake_bundle or {})
    expected_token = str(current.get("confirmation_token", "") or "")
    if not expected_token or provided_token != expected_token:
        reasons = sorted(
            set([str(x) for x in list(current.get("reason_codes") or []) if str(x or "").strip()])
            | {"invalid_confirmation_token"}
        )
        return {
            **current,
            "state": "pending_confirmation",
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "receipt_id": "",
            "reason_codes": reasons,
        }

    action_rows = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    available_action_ids = [
        str(row.get("action_id", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    ]
    if decision == "cancel":
        reasons = sorted(
            set([str(x) for x in list(current.get("reason_codes") or []) if str(x or "").strip()])
            | {"user_cancelled"}
        )
        return {
            **current,
            "state": "cancelled",
            "requires_confirmation": False,
            "approved_action_ids": [],
            "blocked_action_ids": available_action_ids,
            "receipt_id": "",
            "reason_codes": reasons,
        }

    if requested_raw is None:
        requested_set = set(available_action_ids)
    else:
        requested_set = set(requested_action_ids)
    approved = [aid for aid in available_action_ids if aid in requested_set]
    blocked = [aid for aid in available_action_ids if aid not in set(approved)]
    state = "approved" if approved else "pending_confirmation"
    reasons = sorted(
        set([str(x) for x in list(current.get("reason_codes") or []) if str(x or "").strip()])
        | ({"user_approved"} if approved else {"no_matching_action_ids"})
    )
    return {
        **current,
        "state": state,
        "requires_confirmation": False if approved else True,
        "approved_action_ids": approved,
        "blocked_action_ids": blocked,
        "receipt_id": "",
        "reason_codes": reasons,
    }


def _apply_execution_idempotency_guard(
    *,
    transition_input: dict[str, object],
    workspace_id: str,
    plan_id: str,
    prior_record: dict[str, object] | None = None,
    persist: bool = True,
) -> tuple[dict[str, object], dict[str, object]]:
    normalized = dict(transition_input or {})
    decision = str(normalized.get("decision", "") or "")
    idem_key = str(normalized.get("idempotency_key", "") or "").strip()
    if not decision:
        return normalized, {
            "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
            "status": "not_applicable",
            "idempotency_key": idem_key,
            "operation_fingerprint": "",
            "guard_action": "none",
            "reason_codes": ["no_transition_decision"],
        }
    if not idem_key:
        return normalized, {
            "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
            "status": "missing_key",
            "idempotency_key": "",
            "operation_fingerprint": "",
            "guard_action": "warning_only",
            "reason_codes": ["idempotency_key_missing"],
        }

    requested = [str(x) for x in list(normalized.get("requested_action_ids") or []) if str(x)]
    token = str(normalized.get("confirmation_token", "") or "")
    seed = f"{workspace_id}|{plan_id}|{decision}|{token}|{','.join(sorted(requested))}"
    fingerprint = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    if not persist:
        return normalized, {
            "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
            "status": "dry_run",
            "idempotency_key": idem_key,
            "operation_fingerprint": fingerprint,
            "guard_action": "none",
            "reason_codes": ["idempotency_evaluation_deferred"],
        }
    prior = dict(prior_record or {})
    prior_key = str(prior.get("idempotency_key", "") or "")
    prior_fingerprint = str(prior.get("operation_fingerprint", "") or "")
    if prior_key and prior_key == idem_key and prior_fingerprint:
        if prior_fingerprint == fingerprint:
            return normalized, {
                "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
                "status": "replayed",
                "idempotency_key": idem_key,
                "operation_fingerprint": fingerprint,
                "guard_action": "recovered_from_durable_replay",
                "reason_codes": ["idempotency_replay_recovered_from_durable"],
            }
        normalized["decision"] = ""
        normalized["requested_action_ids"] = []
        return normalized, {
            "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
            "status": "conflict",
            "idempotency_key": idem_key,
            "operation_fingerprint": fingerprint,
            "guard_action": "blocked_durable_conflict",
            "reason_codes": ["idempotency_conflict_blocked"],
        }

    prev = _EXECUTION_IDEMPOTENCY_SEEN.get(idem_key)
    if prev is None:
        _EXECUTION_IDEMPOTENCY_SEEN[idem_key] = fingerprint
        status = "fresh"
        guard_action = "recorded"
        reason_codes = ["idempotency_recorded"]
    elif prev == fingerprint:
        status = "replayed"
        guard_action = "short_circuit_replay_safe"
        reason_codes = ["idempotency_replay_detected"]
    else:
        normalized["decision"] = ""
        normalized["requested_action_ids"] = []
        status = "conflict"
        guard_action = "blocked_conflict"
        reason_codes = ["idempotency_conflict_blocked"]

    return normalized, {
        "contract_version": EXECUTION_IDEMPOTENCY_CONTRACT_VERSION,
        "status": status,
        "idempotency_key": idem_key,
        "operation_fingerprint": fingerprint,
        "guard_action": guard_action,
        "reason_codes": reason_codes,
    }


def _build_transition_policy_contract() -> dict[str, object]:
    return {
        "mode": "confirmation_guarded",
        "require_confirmation_token": True,
        "allow_partial_approval": True,
        "max_approved_action_ids": EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        "allowlisted_action_types": list(EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES),
        "allowlisted_action_pattern": EXECUTION_PILOT_ALLOWLISTED_ACTION_PATTERN,
        "enforce_allowlisted_action_types": True,
        "allowed_decisions": ["approve", "cancel"],
    }


def _apply_handshake_transition_policy(
    *,
    transition_input: dict[str, object],
    draft_actions_bundle: dict[str, object],
    policy_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    normalized = dict(transition_input or {})
    decision = str(normalized.get("decision", "") or "")
    requested_action_ids = [str(x) for x in list(normalized.get("requested_action_ids") or []) if str(x)]
    action_rows = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    available_action_ids = [
        str(row.get("action_id", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    ]
    action_type_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("action_type", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }
    available_set = set(available_action_ids)
    policy_reasons: list[str] = []
    blocked_non_allowlisted_action_ids: list[str] = []
    unknown_ids = [x for x in requested_action_ids if x not in available_set]
    if unknown_ids:
        policy_reasons.append("unknown_action_ids_blocked")
    requested_action_ids = [x for x in requested_action_ids if x in available_set]

    if decision == "cancel" and requested_action_ids:
        requested_action_ids = []
        policy_reasons.append("cancel_ignores_action_filter")

    max_ids = int(policy_contract.get("max_approved_action_ids", 3) or 3)
    allowlisted_action_types = [
        str(x).strip()
        for x in list(policy_contract.get("allowlisted_action_types") or [])
        if str(x or "").strip()
    ]
    allowlisted_set = set(allowlisted_action_types)
    enforce_allowlisted_action_types = bool(policy_contract.get("enforce_allowlisted_action_types", False))
    if decision == "approve" and enforce_allowlisted_action_types:
        blocked_non_allowlisted_action_ids = [
            aid
            for aid in requested_action_ids
            if not _is_allowlisted_pilot_action_type(
                str(action_type_by_id.get(aid, "") or ""),
                allowlisted_set,
            )
        ]
        if blocked_non_allowlisted_action_ids:
            requested_action_ids = [aid for aid in requested_action_ids if aid not in set(blocked_non_allowlisted_action_ids)]
            policy_reasons.append("non_allowlisted_action_types_blocked")
    if decision == "approve" and len(requested_action_ids) > max_ids:
        requested_action_ids = requested_action_ids[:max_ids]
        policy_reasons.append("approval_limit_applied")

    normalized["requested_action_ids"] = requested_action_ids
    policy_eval = {
        **dict(policy_contract or {}),
        "requested_action_ids_count": len(requested_action_ids),
        "available_action_ids_count": len(available_action_ids),
        "unknown_action_ids": unknown_ids,
        "blocked_non_allowlisted_action_ids": blocked_non_allowlisted_action_ids,
        "rollback_contract_status": "not_evaluated",
        "rollback_missing_action_ids": [],
        "applied_reason_codes": sorted(set(policy_reasons)),
    }
    return normalized, policy_eval


def _apply_durable_confirmation_token_guards(
    *,
    transition_input: dict[str, object],
    durable_approval_record: dict[str, object],
) -> tuple[dict[str, object], list[str]]:
    normalized = dict(transition_input or {})
    decision = str(normalized.get("decision", "") or "")
    if not decision:
        return normalized, []

    record = dict(durable_approval_record or {})
    provided_token = str(normalized.get("confirmation_token", "") or "")
    stored_token = str(record.get("confirmation_token", "") or "")
    if not provided_token or not stored_token or provided_token != stored_token:
        return normalized, []

    reasons: list[str] = []
    try:
        expires_at = int(str(record.get("token_expires_at", "") or "0") or "0")
    except Exception:
        expires_at = 0
    now_ts = int(time.time())
    if expires_at > 0 and now_ts >= expires_at:
        reasons.append("confirmation_token_expired")

    last_decision = str(record.get("last_decision", "") or "")
    if last_decision in {"approve", "cancel"}:
        reasons.append("confirmation_token_consumed")

    if reasons:
        normalized["decision"] = ""
        normalized["requested_action_ids"] = []
    return normalized, sorted(set(reasons))


def _apply_rollback_contract_guard(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    handshake = dict(handshake_bundle or {})
    state = str(handshake.get("state", "idle") or "idle")
    approved_action_ids = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    action_rows = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    rollback_by_action_id = {
        str(row.get("action_id", "") or ""): str(row.get("rollback_plan", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }

    if state != "approved":
        return handshake, {
            "status": "not_applicable",
            "rollback_required_action_ids": [],
            "rollback_ready_action_ids": [],
            "rollback_missing_action_ids": [],
            "reason_codes": [],
        }

    rollback_ready_action_ids = [
        aid
        for aid in approved_action_ids
        if str(rollback_by_action_id.get(aid, "") or "").strip()
    ]
    rollback_missing_action_ids = [aid for aid in approved_action_ids if aid not in set(rollback_ready_action_ids)]
    if not rollback_missing_action_ids:
        return handshake, {
            "status": "ready",
            "rollback_required_action_ids": approved_action_ids,
            "rollback_ready_action_ids": rollback_ready_action_ids,
            "rollback_missing_action_ids": [],
            "reason_codes": ["rollback_contract_validated"],
        }

    prior_reasons = [str(x) for x in list(handshake.get("reason_codes") or []) if str(x or "").strip()]
    guarded_handshake = {
        **handshake,
        "state": "pending_confirmation",
        "requires_confirmation": True,
        "approved_action_ids": [],
        "blocked_action_ids": sorted(
            set([str(x) for x in list(handshake.get("blocked_action_ids") or []) if str(x)] + rollback_missing_action_ids)
        ),
        "receipt_id": "",
        "reason_codes": sorted(set(prior_reasons + ["rollback_contract_missing_for_approved_actions"])),
    }
    return guarded_handshake, {
        "status": "blocked_missing_rollback_plan",
        "rollback_required_action_ids": approved_action_ids,
        "rollback_ready_action_ids": rollback_ready_action_ids,
        "rollback_missing_action_ids": rollback_missing_action_ids,
        "reason_codes": ["rollback_contract_missing_for_approved_actions"],
    }


def _run_execution_pilot_runtime(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    actions_enabled: bool,
) -> tuple[list[str], list[str]]:
    handshake = dict(handshake_bundle or {})
    if not actions_enabled:
        return [], ["pilot_runtime_disabled"]
    if str(handshake.get("state", "idle") or "idle") != "approved":
        return [], ["pilot_runtime_not_approved"]

    approved_action_ids = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    if not approved_action_ids:
        return [], ["pilot_runtime_no_approved_actions"]

    action_rows = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    action_type_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("action_type", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }
    rollback_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("rollback_plan", "") or "")
        for row in action_rows
        if str(row.get("action_id", "") or "").strip()
    }
    allowlisted_set = set(EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES)
    eligible = [
        aid
        for aid in approved_action_ids
        if _is_allowlisted_pilot_action_type(str(action_type_by_id.get(aid, "") or ""), allowlisted_set)
        and bool(str(rollback_by_id.get(aid, "") or "").strip())
    ]
    executed_action_ids = eligible[: int(EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS)]
    if executed_action_ids:
        return executed_action_ids, ["pilot_runtime_executed"]
    return [], ["pilot_runtime_no_eligible_actions"]


def _build_execution_receipt_stub(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
    executed_action_ids: list[str] | None = None,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    plan_id = str(plan_bundle.get("plan_id", "") or "")
    state = str(handshake.get("state", "idle") or "idle")
    approved = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    blocked = [str(x) for x in list(handshake.get("blocked_action_ids") or []) if str(x)]
    rollback_by_action_id = {
        str((row or {}).get("action_id", "") or ""): str((row or {}).get("rollback_plan", "") or "")
        for row in list(draft_actions_bundle.get("actions") or [])
        if str((row or {}).get("action_id", "") or "").strip()
    }
    rollback_required_action_ids = approved if state == "approved" else []
    rollback_ready_action_ids = [
        aid for aid in rollback_required_action_ids if str(rollback_by_action_id.get(aid, "") or "").strip()
    ]
    rollback_missing_action_ids = [
        aid for aid in rollback_required_action_ids if aid not in set(rollback_ready_action_ids)
    ]
    rollback_status = (
        "ready"
        if state == "approved" and not rollback_missing_action_ids
        else ("blocked_missing_rollback_plan" if state == "approved" else "not_applicable")
    )
    if not blocked:
        blocked = [
            str((row or {}).get("action_id", "") or "")
            for row in list(draft_actions_bundle.get("actions") or [])
            if str((row or {}).get("action_id", "") or "").strip()
            and str((row or {}).get("action_id", "") or "") not in set(approved)
        ]

    executed = [str(x) for x in list(executed_action_ids or []) if str(x)]
    if state in {"approved", "cancelled"}:
        seed = f"{workspace_id}|{request_id}|{plan_id}|{state}|{','.join(sorted(approved))}|{','.join(sorted(blocked))}"
        receipt_id = f"receipt:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
        status = "recorded"
        reason_codes = ["execution_receipt_stub_recorded"]
        if executed:
            reason_codes.append("pilot_runtime_execution_recorded")
    elif state == "pending_confirmation":
        receipt_id = ""
        status = "awaiting_confirmation"
        reason_codes = ["execution_receipt_pending_confirmation"]
    else:
        receipt_id = ""
        status = "idle"
        reason_codes = ["execution_receipt_not_ready"]

    return {
        "contract_version": EXECUTION_RECEIPT_CONTRACT_VERSION,
        "receipt_id": receipt_id,
        "status": status,
        "handshake_state": state,
        "plan_id": plan_id,
        "approved_action_ids": approved,
        "blocked_action_ids": blocked,
        "executed_action_ids": executed,
        "rollback_status": rollback_status,
        "rollback_required_action_ids": rollback_required_action_ids,
        "rollback_ready_action_ids": rollback_ready_action_ids,
        "rollback_missing_action_ids": rollback_missing_action_ids,
        "reason_codes": reason_codes,
    }


def _build_safe_mode_execution_gateway(
    *,
    handshake_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    receipt = dict(receipt_bundle or {})
    state = str(handshake.get("state", "idle") or "idle")
    approved = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    blocked = [str(x) for x in list(handshake.get("blocked_action_ids") or []) if str(x)]
    if not actions_enabled:
        return {
            "contract_version": EXECUTION_GATEWAY_CONTRACT_VERSION,
            "mode": "safe_mode",
            "state": "disabled",
            "safe_mode": True,
            "approved_action_ids": [],
            "blocked_action_ids": [],
            "executed_action_ids": [],
            "dry_run_action_ids": [],
            "reason_codes": ["assistant_actions_disabled"],
        }
    if state == "approved":
        executed = [str(x) for x in list(receipt.get("executed_action_ids") or []) if str(x)]
        if executed:
            return {
                "contract_version": EXECUTION_GATEWAY_CONTRACT_VERSION,
                "mode": "safe_mode",
                "state": "executed_in_pilot",
                "safe_mode": True,
                "approved_action_ids": approved,
                "blocked_action_ids": blocked,
                "executed_action_ids": executed,
                "dry_run_action_ids": [],
                "reason_codes": ["pilot_runtime_executed_no_external_side_effects"],
            }
        return {
            "contract_version": EXECUTION_GATEWAY_CONTRACT_VERSION,
            "mode": "safe_mode",
            "state": "ready_for_execution",
            "safe_mode": True,
            "approved_action_ids": approved,
            "blocked_action_ids": blocked,
            "executed_action_ids": [],
            "dry_run_action_ids": approved,
            "reason_codes": ["execution_safe_mode_no_side_effects"],
        }
    if state == "cancelled":
        return {
            "contract_version": EXECUTION_GATEWAY_CONTRACT_VERSION,
            "mode": "safe_mode",
            "state": "cancelled",
            "safe_mode": True,
            "approved_action_ids": [],
            "blocked_action_ids": blocked,
            "executed_action_ids": [],
            "dry_run_action_ids": [],
            "reason_codes": ["execution_cancelled_by_user"],
        }
    if str(receipt.get("status", "") or "") == "awaiting_confirmation":
        gateway_state = "awaiting_confirmation"
        reasons = ["execution_awaiting_confirmation"]
    else:
        gateway_state = "idle"
        reasons = ["execution_gateway_idle"]
    return {
        "contract_version": EXECUTION_GATEWAY_CONTRACT_VERSION,
        "mode": "safe_mode",
        "state": gateway_state,
        "safe_mode": True,
        "approved_action_ids": approved,
        "blocked_action_ids": blocked,
        "executed_action_ids": [],
        "dry_run_action_ids": [],
        "reason_codes": reasons,
    }


def _build_execution_pilot_bundle(
    *,
    handshake_bundle: dict[str, object],
    draft_actions_bundle: dict[str, object],
    receipt_bundle: dict[str, object],
    actions_enabled: bool,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    receipt = dict(receipt_bundle or {})
    requested_action_ids = [str(x) for x in list(handshake.get("approved_action_ids") or []) if str(x)]
    executed_action_ids = [str(x) for x in list(receipt.get("executed_action_ids") or []) if str(x)]
    actions = [dict(row or {}) for row in list(draft_actions_bundle.get("actions") or [])]
    action_type_by_id = {
        str(row.get("action_id", "") or ""): str(row.get("action_type", "") or "")
        for row in actions
        if str(row.get("action_id", "") or "").strip()
    }
    allowed_action_types = list(EXECUTION_PILOT_ALLOWLISTED_ACTION_TYPES)
    if not actions_enabled:
        return {
            "contract_version": EXECUTION_PILOT_CONTRACT_VERSION,
            "mode": "controlled_pilot",
            "state": "disabled",
            "safe_mode": True,
            "execute_enabled": False,
            "max_actions_per_run": EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
            "allowed_action_types": allowed_action_types,
            "requested_action_ids": requested_action_ids,
            "eligible_action_ids": [],
            "blocked_action_ids": [],
            "executed_action_ids": [],
            "reason_codes": ["assistant_actions_disabled"],
        }

    allowlisted_set = set(allowed_action_types)
    eligible = [
        aid
        for aid in requested_action_ids
        if _is_allowlisted_pilot_action_type(str(action_type_by_id.get(aid, "") or ""), allowlisted_set)
    ]
    blocked = [aid for aid in requested_action_ids if aid not in set(eligible)]
    state = str(handshake.get("state", "idle") or "idle")
    if executed_action_ids:
        pilot_state = "executed"
        reasons = ["pilot_runtime_executed"]
    elif state == "pending_confirmation":
        pilot_state = "awaiting_confirmation"
        reasons = ["pilot_waiting_confirmation"]
    elif eligible:
        pilot_state = "ready"
        reasons = ["pilot_candidates_ready"]
    elif requested_action_ids:
        pilot_state = "blocked"
        reasons = ["pilot_action_type_not_allowlisted"]
    else:
        pilot_state = "idle"
        reasons = ["pilot_no_approved_actions"]
    return {
        "contract_version": EXECUTION_PILOT_CONTRACT_VERSION,
        "mode": "controlled_pilot",
        "state": pilot_state,
        "safe_mode": True,
        "execute_enabled": False,
        "max_actions_per_run": EXECUTION_PILOT_MAX_APPROVED_ACTION_IDS,
        "allowed_action_types": allowed_action_types,
        "requested_action_ids": requested_action_ids,
        "eligible_action_ids": eligible[:1],
        "blocked_action_ids": blocked,
        "executed_action_ids": executed_action_ids,
        "reason_codes": reasons,
    }


def _build_approval_session_bundle(
    *,
    handshake_bundle: dict[str, object],
    plan_bundle: dict[str, object],
    workspace_id: str,
    request_id: str,
) -> dict[str, object]:
    handshake = dict(handshake_bundle or {})
    state = str(handshake.get("state", "idle") or "idle")
    plan_id = str(plan_bundle.get("plan_id", "") or "")
    if state == "pending_confirmation":
        seed = f"{workspace_id}|{request_id}|{plan_id}|pending"
        approval_id = f"approval:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
        token = str(handshake.get("confirmation_token", "") or "")
        return {
            "contract_version": APPROVAL_SESSION_CONTRACT_VERSION,
            "approval_id": approval_id,
            "workspace_id": str(workspace_id or ""),
            "plan_id": plan_id,
            "status": "open",
            "requires_confirmation": True,
            "one_time_token": token,
            "token_ttl_seconds": 900,
            "reason_codes": ["approval_session_opened"],
        }
    if state in {"approved", "cancelled", "executed"}:
        return {
            "contract_version": APPROVAL_SESSION_CONTRACT_VERSION,
            "approval_id": "",
            "workspace_id": str(workspace_id or ""),
            "plan_id": plan_id,
            "status": "closed",
            "requires_confirmation": False,
            "one_time_token": "",
            "token_ttl_seconds": 0,
            "reason_codes": ["approval_session_closed"],
        }
    return {
        "contract_version": APPROVAL_SESSION_CONTRACT_VERSION,
        "approval_id": "",
        "workspace_id": str(workspace_id or ""),
        "plan_id": plan_id,
        "status": "idle",
        "requires_confirmation": False,
        "one_time_token": "",
        "token_ttl_seconds": 0,
        "reason_codes": ["approval_session_idle"],
    }


def _build_durable_approval_session_record(
    *,
    approval_session_bundle: dict[str, object],
    session_id: str,
    confirmation_token: str,
    transition_input: dict[str, object],
    previous_record: dict[str, object] | None = None,
) -> dict[str, object]:
    approval = dict(approval_session_bundle or {})
    previous = dict(previous_record or {})
    status = str(approval.get("status", "idle") or "idle")
    ttl = int(approval.get("token_ttl_seconds", 0) or 0)
    token = str(confirmation_token or previous.get("confirmation_token", "") or "")
    prev_exp = str(previous.get("token_expires_at", "") or "")
    token_expires_at = prev_exp
    if status == "open" and token:
        if not token_expires_at:
            token_expires_at = str(int(time.time()) + ttl if ttl > 0 else 0)
        last_decision = ""
    elif status == "closed":
        current_decision = str(transition_input.get("decision", "") or "")
        previous_decision = str(previous.get("last_decision", "") or "")
        last_decision = current_decision if current_decision in {"approve", "cancel"} else previous_decision
    else:
        last_decision = str(previous.get("last_decision", "") or "")
    return {
        "contract_version": DURABLE_APPROVAL_SESSION_CONTRACT_VERSION,
        "approval_id": str(approval.get("approval_id", "") or ""),
        "workspace_id": str(approval.get("workspace_id", "") or ""),
        "session_id": str(session_id or "default"),
        "plan_id": str(approval.get("plan_id", "") or ""),
        "status": status,
        "confirmation_token": token,
        "token_expires_at": token_expires_at,
        "last_decision": last_decision,
        "reason_codes": ["durable_record_not_persisted_yet"],
    }


def _build_idempotency_record_snapshot(
    *,
    execution_idempotency_bundle: dict[str, object],
    workspace_id: str,
    plan_id: str,
    transition_input: dict[str, object],
) -> dict[str, object]:
    idem = dict(execution_idempotency_bundle or {})
    return {
        "contract_version": IDEMPOTENCY_RECORD_CONTRACT_VERSION,
        "idempotency_key": str(idem.get("idempotency_key", "") or ""),
        "workspace_id": str(workspace_id or ""),
        "plan_id": str(plan_id or ""),
        "operation_fingerprint": str(idem.get("operation_fingerprint", "") or ""),
        "status": str(idem.get("status", "none") or "none"),
        "confirmation_token": str(transition_input.get("confirmation_token", "") or ""),
        "decision": str(transition_input.get("decision", "") or ""),
        "reason_codes": ["durable_record_not_persisted_yet"],
    }


async def _load_durable_records(
    *,
    req: AnswerRequest,
    workspace_id: str,
    get_memory_store: object,
) -> tuple[dict[str, object], dict[str, object]]:
    sid = str(getattr(req, "session_id", "") or "default")
    mem = get_memory_store()
    approval_raw = ""
    try:
        mem_get = getattr(mem, "get", None)
        if callable(mem_get):
            approval_raw = await mem_get(
                workspace_id=workspace_id,
                key=_durable_approval_record_key(session_id=sid),
            )
    except Exception:
        approval_raw = ""
    approval_loaded: dict[str, object] = {}
    try:
        approval_loaded = dict(json.loads(str(approval_raw or "")) or {})
    except Exception:
        approval_loaded = {}

    idem_from_filters = str((dict(getattr(req, "filters", {}) or {})).get("handshake_idempotency_key", "") or "")
    idem_raw = ""
    try:
        mem_get = getattr(mem, "get", None)
        if callable(mem_get):
            idem_raw = await mem_get(
                workspace_id=workspace_id,
                key=_durable_idempotency_record_key(session_id=sid, idempotency_key=idem_from_filters),
            )
    except Exception:
        idem_raw = ""
    idempotency_loaded: dict[str, object] = {}
    try:
        idempotency_loaded = dict(json.loads(str(idem_raw or "")) or {})
    except Exception:
        idempotency_loaded = {}
    return approval_loaded, idempotency_loaded


def _hydrate_durable_records_into_diagnostics(
    *,
    diagnostics: dict[str, object],
    loaded_approval: dict[str, object],
    loaded_idempotency: dict[str, object],
) -> None:
    current_approval = dict(diagnostics.get("assistant_durable_approval_session") or {})
    current_idem = dict(diagnostics.get("assistant_idempotency_record") or {})
    if loaded_approval and not str(current_approval.get("approval_id", "") or ""):
        reasons = sorted(
            set([str(x) for x in list(loaded_approval.get("reason_codes") or []) if str(x)] + ["loaded_from_durable_store"])
        )
        diagnostics["assistant_durable_approval_session"] = {
            **loaded_approval,
            "reason_codes": reasons,
        }
    if loaded_idempotency and not str(current_idem.get("idempotency_key", "") or ""):
        reasons = sorted(
            set([str(x) for x in list(loaded_idempotency.get("reason_codes") or []) if str(x)] + ["loaded_from_durable_store"])
        )
        diagnostics["assistant_idempotency_record"] = {
            **loaded_idempotency,
            "reason_codes": reasons,
        }


async def _persist_durable_records(
    *,
    req: AnswerRequest,
    resp: object,
    workspace_id: str,
    get_memory_store: object,
) -> None:
    diag = dict(getattr(resp, "diagnostics", None) or {})
    approval_record = dict(diag.get("assistant_durable_approval_session") or {})
    idempotency_record = dict(diag.get("assistant_idempotency_record") or {})
    sid = str(getattr(req, "session_id", "") or "default")
    mem = get_memory_store()
    await mem.put(
        workspace_id=workspace_id,
        key=_durable_approval_record_key(session_id=sid),
        value=json.dumps(approval_record, ensure_ascii=True, sort_keys=True),
        metadata={"session_id": sid, "kind": "durable_approval_session_record"},
    )
    idem_key = str(idempotency_record.get("idempotency_key", "") or "")
    await mem.put(
        workspace_id=workspace_id,
        key=_durable_idempotency_record_key(session_id=sid, idempotency_key=idem_key),
        value=json.dumps(idempotency_record, ensure_ascii=True, sort_keys=True),
        metadata={"session_id": sid, "kind": "durable_idempotency_record"},
    )


def log_observability(http: Request, *, workspace_id: str, req: AnswerRequest) -> None:
    try:
        from loguru import logger

        rid = get_request_id(http)
        logger.info(
            "answer.endpoint request_id={} workspace={} qlen={} k={} depth={}",
            rid,
            workspace_id,
            len(req.query or ""),
            int(req.k or 0),
            int(req.graph_depth or 0),
        )
    except Exception:
        pass


async def _apply_diagnostics(
    *,
    resp: Any,
    req: AnswerRequest,
    http: Request,
    workspace_id: str,
    retriever: object,
    llm: object | None,
    llm_enabled: bool,
    llm_provider_name: str,
    llm_model: str,
    llm_error: str,
    assistant_mode_enabled: bool,
    assistant_proactive_enabled: bool,
    assistant_actions_enabled: bool,
    assistant_response_language: str,
    session_memory_loaded: bool,
    session_memory_hit: bool,
) -> None:
    try:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        diag.setdefault("retrieved_provenance_count", int(len(getattr(resp, "provenance", []) or [])))
        diag.setdefault("used_chunks_count", int(len(getattr(resp, "used_chunks", []) or [])))
        diag.setdefault("used_nodes_count", int(len(getattr(resp, "used_nodes", []) or [])))
        diag.setdefault("used_edges_count", int(len(getattr(resp, "used_edges", []) or [])))
        diag.setdefault("has_llm", bool(llm is not None))
        diag.setdefault("query_len", int(len(req.query or "")))
        diag.setdefault("k", int(req.k or 0))
        diag.setdefault("graph_depth", int(req.graph_depth or 0))
        diag.setdefault("session_id", str(getattr(req, "session_id", "") or ""))
        diag.setdefault("evidence_contract_version", EVIDENCE_CONTRACT_VERSION)
        contract = dict(diag.get("evidence_contract") or {})
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
            int(contract.get("missing_minimal_count") or len(contract.get("missing_minimal_fields") or [])),
        )
        diag.setdefault(
            "evidence_contract_minimal_coverage_score",
            float(contract.get("minimal_coverage_score") or 0.0),
        )
        if bool(diag.get("evidence_contract_valid_minimal", False)):
            diag.setdefault("evidence_contract_gate_reason", "ok")
        else:
            missing = list(diag.get("evidence_contract_missing_minimal_fields") or [])
            if missing:
                diag.setdefault("evidence_contract_gate_reason", "missing:" + ",".join(str(x) for x in missing))
            else:
                diag.setdefault("evidence_contract_gate_reason", "invalid")
        diag.setdefault(
            "self_check",
            {
                "version": "v1",
                "status": (
                    "pass"
                    if (
                        float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                        >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                        and int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                        <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                    )
                    else "warn"
                ),
                "reasons": (
                    []
                    if (
                        float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                        >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                        and int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                        <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                    )
                    else [
                        *(
                            [
                                f"threshold:minimal_coverage_score<{float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN):.1f}"
                            ]
                            if float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
                            < float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
                            else []
                        ),
                        *(
                            [
                                f"threshold:missing_minimal_count>{int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)}"
                            ]
                            if int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
                            > int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
                            else []
                        ),
                    ]
                ),
                "policy_mode": "warning_only",
                "inputs": {
                    "evidence_contract_valid_minimal": bool(
                        diag.get("evidence_contract_valid_minimal", False)
                    ),
                    "evidence_contract_missing_minimal_count": int(
                        diag.get("evidence_contract_missing_minimal_count", 0) or 0
                    ),
                    "evidence_contract_minimal_coverage_score": float(
                        diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0
                    ),
                },
                "thresholds": {
                    "minimal_coverage_score_min": float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN),
                    "missing_minimal_count_max": int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX),
                },
            },
        )
        self_check = dict(diag.get("self_check") or {})
        if str(self_check.get("status", "")) == "warn":
            resp.warnings = list(getattr(resp, "warnings", []) or [])
            if "self_check_warning" not in resp.warnings:
                resp.warnings.append("self_check_warning")
        diag.setdefault(
            "verify",
            {
                "version": VERIFY_DIAGNOSTICS_VERSION,
                "status": (
                    "pass"
                    if (
                        str(self_check.get("status", "") or "")
                        == str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                        and str(self_check.get("policy_mode", "") or "")
                        == str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                        and int(len(self_check.get("reasons") or []))
                        <= int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                    )
                    else "warn"
                ),
                "reasons": (
                    []
                    if (
                        str(self_check.get("status", "") or "")
                        == str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                        and str(self_check.get("policy_mode", "") or "")
                        == str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                        and int(len(self_check.get("reasons") or []))
                        <= int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                    )
                    else [
                        *(
                            [f"self_check_status!={VERIFY_SELF_CHECK_STATUS_REQUIRED}"]
                            if str(self_check.get("status", "") or "")
                            != str(VERIFY_SELF_CHECK_STATUS_REQUIRED)
                            else []
                        ),
                        *(
                            [f"self_check_policy_mode!={VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED}"]
                            if str(self_check.get("policy_mode", "") or "")
                            != str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED)
                            else []
                        ),
                        *(
                            [f"self_check_reasons_count>{int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)}"]
                            if int(len(self_check.get("reasons") or []))
                            > int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)
                            else []
                        ),
                    ]
                ),
                "policy_mode": "warning_only",
                "inputs": {
                    "planner_path_used": bool(diag.get("planner_path_used", False)),
                    "self_check_status": str(self_check.get("status", "") or ""),
                    "self_check_policy_mode": str(self_check.get("policy_mode", "") or ""),
                    "self_check_reasons_count": int(len(self_check.get("reasons") or [])),
                },
                "thresholds": {
                    "required_self_check_status": str(VERIFY_SELF_CHECK_STATUS_REQUIRED),
                    "required_self_check_policy_mode": str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED),
                    "self_check_reasons_count_max": int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX),
                },
            },
        )
        verify = dict(diag.get("verify") or {})
        if str(verify.get("status", "")) == "warn":
            resp.warnings = list(getattr(resp, "warnings", []) or [])
            if "verify_warning" not in resp.warnings:
                resp.warnings.append("verify_warning")
        coverage_score = float(diag.get("evidence_contract_minimal_coverage_score", 0.0) or 0.0)
        missing_claims = int(diag.get("evidence_contract_missing_minimal_count", 0) or 0)
        raw_conf = max(0.0, min(1.0, coverage_score - float(missing_claims * 0.15)))
        policy = build_reasoning_execution_policy()
        max_retries = int(policy.get("max_retries", 0) or 0)
        retry_budget_available = bool(raw_conf < 0.6 and max_retries > 0)
        diag.setdefault("reasoning_execution_policy", dict(policy))
        diag.setdefault(
            "reasoning_quality",
            {
                "version": "v1",
                "claims_total": 0,
                "claims_sample": [],
                "coverage": {
                    "claims_total": 0,
                    "claims_covered": 0,
                    "claims_uncovered": 0,
                    "coverage_score": coverage_score,
                    "covered_claim_indices": [],
                    "uncovered_claim_indices": [],
                },
                "confidence": {
                    "coverage_score": coverage_score,
                    "unsupported_claims": 0,
                    "missing_claims": missing_claims,
                    "penalty_unsupported": 0.0,
                    "penalty_missing": float(missing_claims * 0.15),
                    "penalty_total": float(missing_claims * 0.15),
                    "raw_confidence": raw_conf,
                    "confidence_score": raw_conf,
                },
                "retry": {
                    "attempt": 0,
                    "max_retries": max_retries,
                    "confidence_score": raw_conf,
                    "threshold": 0.6,
                    "confidence_below_threshold": bool(raw_conf < 0.6),
                    "retry_budget_available": bool(retry_budget_available),
                    "should_retry": bool(retry_budget_available),
                    "next_attempt": 1 if retry_budget_available else 0,
                    "loop_guard_triggered": False,
                    "reason": (
                        "retry_allowed_low_confidence"
                        if retry_budget_available
                        else "retry_not_needed_confidence_ok"
                    ),
                },
            },
        )
        reasoning_quality = dict(diag.get("reasoning_quality") or {})
        diag.setdefault(
            "reasoning_benchmark",
            {
                "suite_name": "reasoning_runtime_fallback",
                "summary": {
                    "suite_name": "reasoning_runtime_fallback",
                    "total_cases": 0,
                    "passed_cases": 0,
                    "pass_rate": 0.0,
                    "average_score": 0.0,
                    "results": [],
                },
                "failed_case_ids": [],
                "average_latency_ms": 0,
                "results": [],
            },
        )
        diag.setdefault(
            "reasoning_optimization",
            {
                "signal": {
                    "trace_id": str(diag.get("trace_id", "") or ""),
                    "confidence_score": 0.0,
                    "coverage_score": 0.0,
                    "pass_rate": 0.0,
                    "average_latency_ms": 0,
                    "warnings_count": int(len(list(getattr(resp, "warnings", []) or []))),
                    "retry_rate": 0.0,
                    "signal_tags": [],
                },
                "proposals": [],
                "decision": {
                    "decision_id": "optimization_decision:runtime",
                    "action": "defer",
                    "selected_proposal_ids": [],
                    "reason_codes": ["no_proposals"],
                    "confidence": 0.0,
                    "requires_human_review": False,
                },
            },
        )
        diag.setdefault(
            "enterprise_productization",
            {
                "release_gate_policy": {
                    "profile_name": "enterprise_default",
                    "required_checks": [],
                    "blocking_checks": [],
                    "minimum_pass_rate": 0.8,
                    "minimum_average_score": 0.7,
                    "minimum_coverage_ratio": 0.0,
                    "allow_skipped": False,
                    "require_benchmark_summary": True,
                    "require_optimization_review": True,
                    "allowed_warning_codes": [],
                },
                "release_checks": {},
                "readiness": {
                    "profile_name": "enterprise_default",
                    "release_gate_passed": False,
                    "failed_checks": [],
                    "benchmark_pass_rate": 0.0,
                    "benchmark_average_score": 0.0,
                    "optimization_action": "defer",
                    "optimization_requires_review": False,
                    "warnings_count": int(len(list(getattr(resp, "warnings", []) or []))),
                    "readiness_score": 0.0,
                    "reason_codes": [],
                },
                "rollout_decision": {
                    "decision_id": "enterprise_rollout:runtime",
                    "action": "defer",
                    "target_environment": "production",
                    "blocked_by": [],
                    "reason_codes": ["no_runtime_enterprise_inputs"],
                    "confidence": 0.0,
                    "requires_human_approval": True,
                },
            },
        )
        diag.setdefault(
            "meta_cognition",
            {
                "uncertainty": {
                    "status": "low",
                    "uncertainty_score": 0.0,
                    "signals": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
                "gap_map": {
                    "session_id": str(diag.get("session_id", "") or ""),
                    "status": "clear",
                    "total_gaps": 0,
                    "high_priority_gaps": 0,
                    "coverage_score": 1.0,
                    "gaps": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
                "reflection": {
                    "status": "ready",
                    "confidence_score": 1.0,
                    "uncertainty_score": 0.0,
                    "coverage_score": 1.0,
                    "insight_count": 0,
                    "insights": [],
                    "reason_codes": [],
                    "warnings": list(getattr(resp, "warnings", []) or []),
                },
            },
        )
        diag.setdefault(
            "reasoning_trace",
            {
                "query": str(getattr(req, "query", "") or ""),
                "plan": [],
                "steps": [],
                "verify_results": [],
                "quality": reasoning_quality,
                "timeline": {"events": [], "total_duration_ms": 0},
                "answer": str(getattr(resp, "answer", "") or ""),
            },
        )
        diag.setdefault(
            "anticipatory",
            {
                "whisper_receipt": {
                    "run_id": "whisper:pending",
                    "status": "skipped",
                    "safe_mode": True,
                    "duration_ms": 0,
                    "suggestion_count": 0,
                    "reason_codes": ["anticipatory_not_run"],
                    "warnings": [],
                },
                "opportunity_scan": {
                    "status": "idle",
                    "opportunity_score": 0.0,
                    "signals": [],
                    "reason_codes": [],
                    "warnings": [],
                },
                "proactive_suggestions": {
                    "status": "idle",
                    "suggestions": [],
                    "top_suggestion_id": "",
                    "reason_codes": [],
                    "warnings": [],
                },
                "draft_actions": {
                    "status": "idle",
                    "actions": [],
                    "top_action_id": "",
                    "requires_confirmation": False,
                    "reason_codes": [],
                    "warnings": [],
                },
            },
        )
        trace = dict(diag.get("reasoning_trace") or {})
        diag.setdefault(
            "reasoning_timeline",
            dict(trace.get("timeline") or {"events": [], "total_duration_ms": 0}),
        )
        diag.setdefault("session_memory_loaded", bool(session_memory_loaded))
        diag.setdefault("session_memory_hit", bool(session_memory_hit))
        diag.setdefault("evidence_type_counts", {})
        # top_evidence: prefer retriever snapshot; fallback to response used_chunks
        try:
            tops = list(getattr(retriever, "last_top_evidence", []) or [])
        except Exception:
            tops = []
        if not tops:
            try:
                tops = [f"chunk:{x}" for x in (getattr(resp, "used_chunks", []) or [])[:10]]
            except Exception:
                tops = []
        if session_memory_hit:
            sid = str(getattr(req, "session_id", "") or "default")
            tops = [f"memory:session:{sid}:last_answer", *list(tops or [])]
            tops = tops[:10]
        diag.setdefault("top_evidence", tops)
        # trace_id must be present in diagnostics (debug snapshot expects it)
        rid = str(get_request_id(http) or "")
        try:
            from src.observability.trace import make_trace_id

            diag.setdefault(
                "trace_id",
                make_trace_id(
                    workspace_id=str(workspace_id or ""),
                    request_id=rid,
                ),
            )
        except Exception:
            # Fallback: stable correlation id even without tracing deps
            diag.setdefault("trace_id", rid or "")

        # LLM diagnostics
        diag.setdefault("llm_enabled", bool(llm_enabled))
        diag.setdefault("llm_provider", llm_provider_name)
        diag.setdefault("llm_model", llm_model)
        diag.setdefault("llm_error", llm_error)
        diag.setdefault("assistant_contract_version", "v1")
        diag.setdefault("intent_contract_version", INTENT_CONTRACT_VERSION)
        diag.setdefault(
            "response_mode",
            (
                "strict_rag"
                if int(diag.get("retrieved_provenance_count", 0) or 0) > 0
                else "assistant_fallback"
            ),
        )
        diag.setdefault("response_language", str(assistant_response_language or "auto"))
        diag.setdefault("assistant_mode_enabled", bool(assistant_mode_enabled))
        diag.setdefault("assistant_proactive_enabled", bool(assistant_proactive_enabled))
        diag.setdefault("assistant_actions_enabled", bool(assistant_actions_enabled))
        intent = _infer_assistant_intent(
            query=str(getattr(req, "query", "") or ""),
            assistant_mode_enabled=assistant_mode_enabled,
        )
        diag.setdefault(
            "assistant_intent",
            {
                "intent": str(intent.get("intent", "general_query") or "general_query"),
                "confidence": float(intent.get("confidence", 0.0) or 0.0),
                "entities": dict(intent.get("entities") or {}),
                "implicit_tasks": list(intent.get("implicit_tasks") or []),
                "source": str(intent.get("source", "heuristic") or "heuristic"),
            },
        )
        intent, plan, llm_planner = await _build_planner_with_fallback(
            query=str(getattr(req, "query", "") or ""),
            intent_payload=intent,
            assistant_mode_enabled=assistant_mode_enabled,
            llm=llm,
            llm_enabled=bool(llm_enabled),
            llm_model=str(llm_model or ""),
            llm_error=str(llm_error or ""),
        )
        llm_planner_policy = _build_llm_planner_policy_contract()
        intent, plan, llm_planner, llm_planner_policy_eval = _apply_llm_planner_policy_guards(
            intent_payload=intent,
            plan_bundle=plan,
            llm_planner_bundle=llm_planner,
            policy_contract=llm_planner_policy,
            query=str(getattr(req, "query", "") or ""),
            assistant_mode_enabled=assistant_mode_enabled,
        )
        plan, planning_policy = _apply_plan_policy_guards(plan_bundle=plan, max_steps=5)
        mcp_tools = _load_mcp_tools_from_runtime(http)
        tool_selection = _build_tool_selection_bundle(
            plan_bundle=plan,
            assistant_mode_enabled=assistant_mode_enabled,
            mcp_tools=mcp_tools,
        )
        tool_selection_policy = _build_tool_selection_policy_contract()
        tool_selection, tool_selection_policy_eval = _apply_tool_selection_policy_guards(
            tool_selection_bundle=tool_selection,
            policy_contract=tool_selection_policy,
            plan_bundle=plan,
        )
        feedback_learning = _build_feedback_learning_bundle(
            req=req,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        feedback_policy = _build_feedback_policy_contract()
        feedback_learning, feedback_policy_eval = _apply_feedback_policy_guards(
            feedback_bundle=feedback_learning,
            policy_contract=feedback_policy,
        )
        feedback_adaptation = _build_feedback_adaptation_bundle(
            feedback_bundle=feedback_learning,
            intent_bundle=intent,
            plan_bundle=plan,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        adaptation_policy = _build_feedback_adaptation_policy_contract()
        feedback_adaptation, adaptation_policy_eval = _apply_feedback_adaptation_policy_guards(
            adaptation_bundle=feedback_adaptation,
            policy_contract=adaptation_policy,
        )
        diag.setdefault("plan_contract_version", PLAN_CONTRACT_VERSION)
        diag.setdefault("assistant_plan", dict(plan))
        llm_planner["plan_id"] = str(plan.get("plan_id", "") or "")
        diag.setdefault("llm_planner_contract_version", LLM_PLANNER_CONTRACT_VERSION)
        diag.setdefault("assistant_llm_planner", llm_planner)
        diag.setdefault("tool_selection_contract_version", TOOL_SELECTION_CONTRACT_VERSION)
        diag.setdefault("assistant_tool_selection", tool_selection)
        diag.setdefault("tool_selection_policy", tool_selection_policy_eval)
        diag.setdefault("feedback_contract_version", FEEDBACK_CONTRACT_VERSION)
        diag.setdefault("assistant_feedback_learning", feedback_learning)
        diag.setdefault("feedback_policy", feedback_policy_eval)
        diag.setdefault("adaptation_contract_version", ADAPTATION_CONTRACT_VERSION)
        diag.setdefault("assistant_feedback_adaptation", feedback_adaptation)
        diag.setdefault("adaptation_policy", adaptation_policy_eval)
        diag.setdefault("llm_planner_policy", llm_planner_policy_eval)
        diag.setdefault("planning_policy", dict(planning_policy))
        diag = _wire_runtime_diagnostics(diagnostics=diag)
        anticipatory = dict(diag.get("anticipatory") or {})
        draft_actions = dict(anticipatory.get("draft_actions") or {})
        handshake = _build_execution_handshake_bundle(
            plan_bundle=plan,
            draft_actions_bundle=draft_actions,
            assistant_mode_enabled=assistant_mode_enabled,
            actions_enabled=assistant_actions_enabled,
        )
        transition_policy = _build_transition_policy_contract()
        transition_input, transition_policy_eval = _apply_handshake_transition_policy(
            transition_input=_extract_handshake_transition_input(req),
            draft_actions_bundle=draft_actions,
            policy_contract=transition_policy,
        )
        transition_input, execution_idempotency = _apply_execution_idempotency_guard(
            transition_input=transition_input,
            workspace_id=str(workspace_id or ""),
            plan_id=str(plan.get("plan_id", "") or ""),
            persist=False,
        )
        handshake = _apply_handshake_transition(
            handshake_bundle=handshake,
            transition_input=transition_input,
            draft_actions_bundle=draft_actions,
        )
        handshake, rollback_contract_eval = _apply_rollback_contract_guard(
            handshake_bundle=handshake,
            draft_actions_bundle=draft_actions,
        )
        transition_policy_eval["rollback_contract_status"] = str(rollback_contract_eval.get("status", "not_evaluated") or "not_evaluated")
        transition_policy_eval["rollback_missing_action_ids"] = [
            str(x) for x in list(rollback_contract_eval.get("rollback_missing_action_ids") or []) if str(x)
        ]
        transition_policy_eval["applied_reason_codes"] = sorted(
            set(
                [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                + [str(x) for x in list(rollback_contract_eval.get("reason_codes") or []) if str(x)]
            )
        )
        executed_action_ids, pilot_runtime_reasons = _run_execution_pilot_runtime(
            handshake_bundle=handshake,
            draft_actions_bundle=draft_actions,
            actions_enabled=assistant_actions_enabled,
        )
        transition_policy_eval["applied_reason_codes"] = sorted(
            set(
                [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
            )
        )
        receipt = _build_execution_receipt_stub(
            handshake_bundle=handshake,
            plan_bundle=plan,
            draft_actions_bundle=draft_actions,
            workspace_id=str(workspace_id or ""),
            request_id=str(get_request_id(http) or ""),
            executed_action_ids=executed_action_ids,
        )
        approval_session = _build_approval_session_bundle(
            handshake_bundle=handshake,
            plan_bundle=plan,
            workspace_id=str(workspace_id or ""),
            request_id=str(get_request_id(http) or ""),
        )
        durable_approval_record = _build_durable_approval_session_record(
            approval_session_bundle=approval_session,
            session_id=str(getattr(req, "session_id", "") or "default"),
            confirmation_token=str(handshake.get("confirmation_token", "") or ""),
            transition_input=transition_input,
            previous_record={},
        )
        idempotency_record = _build_idempotency_record_snapshot(
            execution_idempotency_bundle=execution_idempotency,
            workspace_id=str(workspace_id or ""),
            plan_id=str(plan.get("plan_id", "") or ""),
            transition_input=transition_input,
        )
        diag.setdefault("execution_handshake_contract_version", HANDSHAKE_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_handshake", handshake)
        diag.setdefault("execution_transition_policy", transition_policy_eval)
        diag.setdefault("execution_idempotency", execution_idempotency)
        diag.setdefault("execution_receipt_contract_version", EXECUTION_RECEIPT_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_receipt", receipt)
        execution_gateway = _build_safe_mode_execution_gateway(
            handshake_bundle=handshake,
            receipt_bundle=receipt,
            actions_enabled=assistant_actions_enabled,
        )
        execution_pilot = _build_execution_pilot_bundle(
            handshake_bundle=handshake,
            draft_actions_bundle=draft_actions,
            receipt_bundle=receipt,
            actions_enabled=assistant_actions_enabled,
        )
        diag.setdefault("execution_gateway_contract_version", EXECUTION_GATEWAY_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_gateway", execution_gateway)
        diag.setdefault("execution_pilot_contract_version", EXECUTION_PILOT_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_pilot", execution_pilot)
        diag.setdefault("approval_session_contract_version", APPROVAL_SESSION_CONTRACT_VERSION)
        diag.setdefault("assistant_approval_session", approval_session)
        diag.setdefault("durable_approval_session_contract_version", DURABLE_APPROVAL_SESSION_CONTRACT_VERSION)
        diag.setdefault("assistant_durable_approval_session", durable_approval_record)
        diag.setdefault("idempotency_record_contract_version", IDEMPOTENCY_RECORD_CONTRACT_VERSION)
        diag.setdefault("assistant_idempotency_record", idempotency_record)
        reason_codes = list(intent.get("reason_codes") or []) + list(plan.get("reason_codes") or [])
        reason_codes.extend(list(llm_planner.get("reason_codes") or []))
        reason_codes.extend(list(tool_selection.get("reason_codes") or []))
        reason_codes.extend(list(tool_selection_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(feedback_learning.get("reason_codes") or []))
        reason_codes.extend(list(feedback_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(feedback_adaptation.get("reason_codes") or []))
        reason_codes.extend(list(adaptation_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(llm_planner_policy_eval.get("applied_reason_codes") or []))
        reason_codes.extend(list(planning_policy.get("reason_codes") or []))
        reason_codes.extend(list(handshake.get("reason_codes") or []))
        reason_codes.extend(list(execution_idempotency.get("reason_codes") or []))
        reason_codes.extend(list(receipt.get("reason_codes") or []))
        reason_codes.extend(list(execution_gateway.get("reason_codes") or []))
        reason_codes.extend(list(execution_pilot.get("reason_codes") or []))
        reason_codes.extend(list(approval_session.get("reason_codes") or []))
        reason_codes.extend(list(durable_approval_record.get("reason_codes") or []))
        reason_codes.extend(list(idempotency_record.get("reason_codes") or []))
        reason_codes = sorted(set([str(x) for x in reason_codes if str(x or "").strip()]))
        diag.setdefault("planning_reason_codes", reason_codes)
        diag.setdefault("plan_id", str(plan.get("plan_id", "") or ""))

        # Memory evidence observability (A2.1)
        try:
            etc = dict(diag.get("evidence_type_counts") or {})
            if session_memory_hit:
                etc["memory"] = int(etc.get("memory", 0)) + 1
            diag["evidence_type_counts"] = etc
        except Exception:
            pass

        # Retriever stats (best-effort)
        try:
            diag.setdefault("retriever_stats", dict(getattr(retriever, "last_stats", {}) or {}))
        except Exception:
            pass

        resp.diagnostics = diag
    except Exception:
        pass


async def _load_session_memory(
    *,
    req: AnswerRequest,
    workspace_id: str,
    get_memory_store: object,
) -> tuple[bool, bool]:
    # A2.1 session memory (MVP): load latest turn per session, best-effort.
    try:
        sid = str(getattr(req, "session_id", "") or "default")
        mem = get_memory_store()
        prev = await mem.get(workspace_id=workspace_id, key=f"session:{sid}:last_answer")
        req.session_memory_last_answer = _clip_text(prev)
        session_memory_loaded = True
        session_memory_hit = bool(req.session_memory_last_answer)
    except Exception:
        req.session_memory_last_answer = ""
        session_memory_loaded = False
        session_memory_hit = False
    return session_memory_loaded, session_memory_hit


async def _save_session_memory(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> None:
    # A2.1 session memory (MVP): persist latest turn per session, best-effort.
    try:
        sid = str(getattr(req, "session_id", "") or "default")
        mem = get_memory_store()
        await mem.put(
            workspace_id=workspace_id,
            key=f"session:{sid}:last_answer",
            value=_clip_text(getattr(resp, "answer", "")),
            metadata={
                "session_id": sid,
                "query": str(getattr(req, "query", "") or ""),
            },
        )
        resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
        resp.diagnostics.setdefault("session_memory_saved", True)
    except Exception:
        try:
            resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
            resp.diagnostics.setdefault("session_memory_saved", False)
        except Exception:
            pass


class _AnticipatorySessionWriter:
    def __init__(self, *, workspace_id: str, session_id: str, get_memory_store: object) -> None:
        self._workspace_id = workspace_id
        self._session_id = session_id
        self._get_memory_store = get_memory_store
        self._buffer: dict[str, object] = {}

    def store(self, *, key: str, value: object) -> None:
        self._buffer[str(key)] = value

    async def flush(self) -> None:
        if not self._buffer:
            return
        mem = self._get_memory_store()
        for key, value in sorted(self._buffer.items(), key=lambda x: str(x[0])):
            await mem.put(
                workspace_id=self._workspace_id,
                key=f"session:{self._session_id}:{str(key)}",
                value=value,
                metadata={"session_id": self._session_id, "kind": str(key)},
            )


async def _run_anticipatory_safe_mode(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
) -> dict[str, object]:
    sid = str(getattr(req, "session_id", "") or "default")
    writer = _AnticipatorySessionWriter(
        workspace_id=workspace_id,
        session_id=sid,
        get_memory_store=get_memory_store,
    )
    context = str(getattr(req, "query", "") or "")
    answer = str(getattr(resp, "answer", "") or "")
    merged_context = f"{context}\n{answer}".strip()
    runner = WhisperRunner(scanner=OpportunityScanner(), safe_mode=True)
    whisper = await runner.run_in_background(
        context=merged_context,
        session_memory=str(getattr(req, "session_memory_last_answer", "") or ""),
        registry=None,
        suggestion_limit=3,
        session_writer=writer,
    )
    await writer.flush()
    raw_suggestions = list(whisper.get("suggestions") or [])
    proactive_rows: list[dict[str, object]] = []
    for row in raw_suggestions:
        item = dict(row or {})
        proactive_rows.append(
            {
                "suggestion_id": str(item.get("suggestion_id", "") or ""),
                "suggestion_type": str(item.get("type", "follow_up") or "follow_up"),
                "confidence": float(item.get("confidence", 0.0) or 0.0),
                "rationale": str(item.get("reason", "") or ""),
                "action_hint": str(item.get("trigger", "") or ""),
                "source_signal_id": str(item.get("suggestion_id", "") or "").replace("suggestion:", ""),
            }
        )
    proactive_bundle = build_proactive_suggestion_bundle(suggestions=proactive_rows, limit=3, warnings=[])
    return {
        "whisper_receipt": dict(whisper.get("receipt") or {}),
        "opportunity_scan": dict(whisper.get("scan") or {}),
        "proactive_suggestions": dict(proactive_bundle),
    }


async def _build_llm_adapter(*, settings: object) -> tuple[object | None, bool, str, str, str]:
    llm_enabled = bool(getattr(settings, "feature_reasoning_llm_enabled", False))
    llm = None
    llm_provider_name = ""
    llm_model = ""
    llm_error = ""

    if llm_enabled:
        try:
            from src.api.dependencies_impl import get_llm_provider

            prov = await get_llm_provider()
            # Determine provider/model for diagnostics in a provider-aware way
            try:
                llm_provider_name = str(getattr(settings, "llm_provider").value)
            except Exception:
                llm_provider_name = str(getattr(settings, "llm_provider", "") or "")
            if llm_provider_name == "openai":
                llm_model = str(getattr(settings, "openai_model", "") or "")
            elif llm_provider_name == "ollama":
                llm_model = str(getattr(settings, "ollama_model", "") or "")
            else:
                llm_model = str(getattr(prov, "model", "") or "")
            llm = LLMGenerateAdapter(prov, provider_name=llm_provider_name, model=llm_model)
        except Exception as e:
            llm = None
            llm_error = str(e)

    return llm, llm_enabled, llm_provider_name, llm_model, llm_error


class RetrieverAdapter:
    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        self._engine = engine
        self._hybrid = hybrid
        self._workspace_id = workspace_id
        self.last_stats: dict[str, object] = {}
        self.last_top_evidence: list[str] = []

    async def retrieve(self, request: AnswerRequest):
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=0.0,
            graph_depth=request.graph_depth,
            evidence_max_total=int(getattr(request, "evidence_max_total", 50) or 50),
            evidence_max_chunks=getattr(request, "evidence_max_chunks", None),
            evidence_max_memory=getattr(request, "evidence_max_memory", None),
            evidence_max_edges=getattr(request, "evidence_max_edges", None),
            evidence_dedupe=bool(getattr(request, "evidence_dedupe", True)),
            evidence_rerank=bool(getattr(request, "evidence_rerank", True)),
        )

        graph = getattr(out, "graph", None)
        evidence = getattr(out, "evidence", None)
        results = getattr(out, "results", None)

        if isinstance(out, dict):
            graph = out.get("graph")
            evidence = out.get("evidence")
            results = out.get("results")

        graph = graph or {"nodes": [], "edges": []}
        evidence = list(evidence or [])
        results = list(results or [])

        # merge retriever stats (best-effort)
        try:
            stats = out.get("stats") if isinstance(out, dict) else getattr(out, "stats", None)
            if isinstance(stats, dict) and stats:
                self.last_stats = dict(self.last_stats or {})
                for k, v in stats.items():
                    self.last_stats.setdefault(str(k), v)
        except Exception:
            pass

        # Hybrid retriever owns evidence policy in A1.5. Keep adapter diagnostics additive only.
        self.last_stats = dict(self.last_stats or {})
        try:
            self.last_stats.setdefault("vector_candidates_count", int(len(results or [])))
            self.last_stats.setdefault("graph_nodes_count", int(len((graph or {}).get("nodes") or [])))
            self.last_stats.setdefault("graph_edges_count", int(len((graph or {}).get("edges") or [])))
            self.last_stats.setdefault("evidence_after_policy_count", int(len(evidence or [])))
        except Exception:
            pass


        # Build debug "top_evidence" list (best-effort). Test expects at least one "chunk:*" when evidence exists.
        try:
            tops: list[str] = []
            for item in (evidence or [])[:10]:
                if isinstance(item, dict):
                    cid = item.get("chunk_id") or item.get("id") or item.get("doc_id")
                    if cid:
                        tops.append(f"chunk:{cid}")
                else:
                    # If evidence is already a string/id-like, keep it as chunk reference
                    s = str(item)
                    if s:
                        tops.append(f"chunk:{s}")
            self.last_top_evidence = tops
        except Exception:
            self.last_top_evidence = []
        return {"results": results, "graph": graph, "evidence": evidence}


class LLMGenerateAdapter:
    """Adapt Base LLM provider (complete/messages) to ReasoningEngine contract (generate(prompt)->str)."""

    def __init__(self, provider: object, *, provider_name: str = "", model: str = ""):
        self._p = provider
        self.provider_name = provider_name
        self.model = model

    async def generate(self, prompt: str) -> str:
        from src.core.types import Message, MessageRole

        messages = [Message(role=MessageRole.USER, content=str(prompt or ""))]
        cfg: dict[str, Any] = {}
        if self.model:
            cfg["model"] = self.model

        if hasattr(self._p, "complete"):
            c = await self._p.complete(messages=messages, config=(cfg or None))
            text = getattr(c, "content", None)
            return str(text if text is not None else c)

        raise RuntimeError("LLM provider does not implement complete()")


class AnswerService:
    """Composition-friendly orchestration for /answer endpoint.

    Keeps FastAPI endpoint thin and concentrates gating/wiring/diagnostics here.
    """

    async def handle(
        self,
        http: Request,
        req,
        *,
        workspace_id: str,
        engine: object | None = None,
        retriever: object | None = None,
    ):
        from src.core.config import get_settings
        from src.core.providers import get_reasoning_engine, get_memory_store

        s = get_settings()
        if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
            # Endpoint uses 404 for feature-gated routes
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        log_observability(http, workspace_id=workspace_id, req=req)

        engine = engine or getattr(http.app.state, "rag_engine", None)
        hybrid = retriever or getattr(http.app.state, "hybrid_retriever", None)
        if engine is None or hybrid is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Reasoning stack not initialized")

        llm, llm_enabled, llm_provider_name, llm_model, llm_error = await _build_llm_adapter(
            settings=s
        )
        assistant_mode_enabled = bool(getattr(s, "feature_assistant_mode", False))
        assistant_proactive_enabled = bool(getattr(s, "feature_assistant_proactive", False))
        assistant_actions_enabled = bool(getattr(s, "feature_assistant_actions", False))
        assistant_response_language = "auto"
        session_memory_loaded = False
        session_memory_hit = False

        session_memory_loaded, session_memory_hit = await _load_session_memory(
            req=req,
            workspace_id=workspace_id,
            get_memory_store=get_memory_store,
        )
        loaded_durable_approval, loaded_durable_idempotency = await _load_durable_records(
            req=req,
            workspace_id=workspace_id,
            get_memory_store=get_memory_store,
        )

        retriever = RetrieverAdapter(engine=engine, hybrid=hybrid, workspace_id=workspace_id)
        reasoning = get_reasoning_engine(retriever=retriever, llm=llm)
        if reasoning is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        t0 = perf_counter()
        resp = await reasoning.synthesize(req)
        total_ms = (perf_counter() - t0) * 1000.0
        if assistant_mode_enabled and not list(getattr(resp, "provenance", []) or []):
            assistant_response_language = _detect_response_language(str(getattr(req, "query", "") or ""))
            resp.answer = _build_assistant_fallback_answer(
                query=str(getattr(req, "query", "") or ""),
                language=assistant_response_language,
            )

        # correlation/timing
        try:
            resp.request_id = get_request_id(http) or ""
        except Exception:
            resp.request_id = ""
        try:
            resp.workspace_id = workspace_id or ""
        except Exception:
            resp.workspace_id = ""

        try:
            resp.timings = dict(resp.timings or {})
            resp.timings.setdefault("total_ms", float(total_ms))
        except Exception:
            pass

        # base diagnostics + trace
        await _apply_diagnostics(
            resp=resp,
            req=req,
            http=http,
            workspace_id=workspace_id,
            retriever=retriever,
            llm=llm,
            llm_enabled=llm_enabled,
            llm_provider_name=llm_provider_name,
            llm_model=llm_model,
            llm_error=llm_error,
            assistant_mode_enabled=assistant_mode_enabled,
            assistant_proactive_enabled=assistant_proactive_enabled,
            assistant_actions_enabled=assistant_actions_enabled,
            assistant_response_language=assistant_response_language,
            session_memory_loaded=session_memory_loaded,
            session_memory_hit=session_memory_hit,
        )
        try:
            if assistant_proactive_enabled:
                anticipatory = await _run_anticipatory_safe_mode(
                    req=req,
                    resp=resp,
                    workspace_id=workspace_id,
                    get_memory_store=get_memory_store,
                )
                anticipatory = dict(anticipatory or {})
                anticipatory["proactive_suggestions"] = _rank_proactive_bundle(
                    dict(anticipatory.get("proactive_suggestions") or {})
                )
                anticipatory["draft_actions"] = _build_draft_action_bundle(
                    proactive_bundle=dict(anticipatory.get("proactive_suggestions") or {}),
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=assistant_actions_enabled,
                )
                diag = dict(getattr(resp, "diagnostics", None) or {})
                diag = _wire_runtime_diagnostics(diagnostics=diag)
                anticipatory["draft_actions"] = _bridge_plan_to_draft_actions(
                    plan_bundle=dict(diag.get("assistant_plan") or {}),
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
                resp.diagnostics["anticipatory"] = anticipatory
                resp.diagnostics = _wire_runtime_diagnostics(diagnostics=resp.diagnostics)
                plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
                handshake = _build_execution_handshake_bundle(
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    assistant_mode_enabled=assistant_mode_enabled,
                    actions_enabled=assistant_actions_enabled,
                )
                transition_policy = _build_transition_policy_contract()
                transition_input, transition_policy_eval = _apply_handshake_transition_policy(
                    transition_input=_extract_handshake_transition_input(req),
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    policy_contract=transition_policy,
                )
                transition_input, token_guard_reasons = _apply_durable_confirmation_token_guards(
                    transition_input=transition_input,
                    durable_approval_record=loaded_durable_approval,
                )
                transition_policy_eval["applied_reason_codes"] = sorted(
                    set(
                        [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                        + list(token_guard_reasons or [])
                    )
                )
                transition_input, execution_idempotency = _apply_execution_idempotency_guard(
                    transition_input=transition_input,
                    workspace_id=str(workspace_id or ""),
                    plan_id=str(plan_bundle.get("plan_id", "") or ""),
                    prior_record=loaded_durable_idempotency,
                )
                handshake = _apply_handshake_transition(
                    handshake_bundle=handshake,
                    transition_input=transition_input,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                )
                handshake, rollback_contract_eval = _apply_rollback_contract_guard(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                )
                transition_policy_eval["rollback_contract_status"] = str(
                    rollback_contract_eval.get("status", "not_evaluated") or "not_evaluated"
                )
                transition_policy_eval["rollback_missing_action_ids"] = [
                    str(x) for x in list(rollback_contract_eval.get("rollback_missing_action_ids") or []) if str(x)
                ]
                transition_policy_eval["applied_reason_codes"] = sorted(
                    set(
                        [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                        + [str(x) for x in list(rollback_contract_eval.get("reason_codes") or []) if str(x)]
                    )
                )
                resp.diagnostics["assistant_execution_handshake"] = handshake
                resp.diagnostics["execution_transition_policy"] = transition_policy_eval
                resp.diagnostics["execution_idempotency"] = execution_idempotency
                executed_action_ids, pilot_runtime_reasons = _run_execution_pilot_runtime(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["execution_transition_policy"]["applied_reason_codes"] = sorted(
                    set(
                        [
                            str(x)
                            for x in list(
                                (dict(resp.diagnostics.get("execution_transition_policy") or {})).get(
                                    "applied_reason_codes", []
                                )
                                or []
                            )
                            if str(x)
                        ]
                        + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
                    )
                )
                resp.diagnostics["assistant_execution_receipt"] = _build_execution_receipt_stub(
                    handshake_bundle=handshake,
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    workspace_id=str(workspace_id or ""),
                    request_id=str(get_request_id(http) or ""),
                    executed_action_ids=executed_action_ids,
                )
                resp.diagnostics["execution_gateway_contract_version"] = EXECUTION_GATEWAY_CONTRACT_VERSION
                resp.diagnostics["assistant_execution_gateway"] = _build_safe_mode_execution_gateway(
                    handshake_bundle=handshake,
                    receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["execution_pilot_contract_version"] = EXECUTION_PILOT_CONTRACT_VERSION
                resp.diagnostics["assistant_execution_pilot"] = _build_execution_pilot_bundle(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["assistant_approval_session"] = _build_approval_session_bundle(
                    handshake_bundle=handshake,
                    plan_bundle=plan_bundle,
                    workspace_id=str(workspace_id or ""),
                    request_id=str(get_request_id(http) or ""),
                )
                resp.diagnostics["durable_approval_session_contract_version"] = DURABLE_APPROVAL_SESSION_CONTRACT_VERSION
                resp.diagnostics["assistant_durable_approval_session"] = _build_durable_approval_session_record(
                    approval_session_bundle=dict(resp.diagnostics.get("assistant_approval_session") or {}),
                    session_id=str(getattr(req, "session_id", "") or "default"),
                    confirmation_token=str(handshake.get("confirmation_token", "") or ""),
                    transition_input=transition_input,
                    previous_record=loaded_durable_approval,
                )
                resp.diagnostics["idempotency_record_contract_version"] = IDEMPOTENCY_RECORD_CONTRACT_VERSION
                resp.diagnostics["assistant_idempotency_record"] = _build_idempotency_record_snapshot(
                    execution_idempotency_bundle=execution_idempotency,
                    workspace_id=str(workspace_id or ""),
                    plan_id=str(plan_bundle.get("plan_id", "") or ""),
                    transition_input=transition_input,
                )
            else:
                resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
                base = dict(resp.diagnostics.get("anticipatory") or {})
                proactive = dict(base.get("proactive_suggestions") or {})
                reason_codes = sorted(
                    set(
                        [
                            str(x)
                            for x in list(proactive.get("reason_codes") or [])
                            if str(x or "").strip()
                        ]
                        + ["assistant_proactive_disabled"]
                    )
                )
                proactive["reason_codes"] = reason_codes
                base["proactive_suggestions"] = proactive
                base["draft_actions"] = _build_draft_action_bundle(
                    proactive_bundle=proactive,
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=False,
                )
                diag = dict(resp.diagnostics or {})
                diag = _wire_runtime_diagnostics(diagnostics=diag)
                base["draft_actions"] = _bridge_plan_to_draft_actions(
                    plan_bundle=dict(diag.get("assistant_plan") or {}),
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["anticipatory"] = base
                resp.diagnostics = _wire_runtime_diagnostics(diagnostics=resp.diagnostics)
                plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
                handshake = _build_execution_handshake_bundle(
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    assistant_mode_enabled=assistant_mode_enabled,
                    actions_enabled=assistant_actions_enabled,
                )
                transition_policy = _build_transition_policy_contract()
                transition_input, transition_policy_eval = _apply_handshake_transition_policy(
                    transition_input=_extract_handshake_transition_input(req),
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    policy_contract=transition_policy,
                )
                transition_input, token_guard_reasons = _apply_durable_confirmation_token_guards(
                    transition_input=transition_input,
                    durable_approval_record=loaded_durable_approval,
                )
                transition_policy_eval["applied_reason_codes"] = sorted(
                    set(
                        [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                        + list(token_guard_reasons or [])
                    )
                )
                transition_input, execution_idempotency = _apply_execution_idempotency_guard(
                    transition_input=transition_input,
                    workspace_id=str(workspace_id or ""),
                    plan_id=str(plan_bundle.get("plan_id", "") or ""),
                    prior_record=loaded_durable_idempotency,
                )
                handshake = _apply_handshake_transition(
                    handshake_bundle=handshake,
                    transition_input=transition_input,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                )
                handshake, rollback_contract_eval = _apply_rollback_contract_guard(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                )
                transition_policy_eval["rollback_contract_status"] = str(
                    rollback_contract_eval.get("status", "not_evaluated") or "not_evaluated"
                )
                transition_policy_eval["rollback_missing_action_ids"] = [
                    str(x) for x in list(rollback_contract_eval.get("rollback_missing_action_ids") or []) if str(x)
                ]
                transition_policy_eval["applied_reason_codes"] = sorted(
                    set(
                        [str(x) for x in list(transition_policy_eval.get("applied_reason_codes") or []) if str(x)]
                        + [str(x) for x in list(rollback_contract_eval.get("reason_codes") or []) if str(x)]
                    )
                )
                resp.diagnostics["assistant_execution_handshake"] = handshake
                resp.diagnostics["execution_transition_policy"] = transition_policy_eval
                resp.diagnostics["execution_idempotency"] = execution_idempotency
                executed_action_ids, pilot_runtime_reasons = _run_execution_pilot_runtime(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["execution_transition_policy"]["applied_reason_codes"] = sorted(
                    set(
                        [
                            str(x)
                            for x in list(
                                (dict(resp.diagnostics.get("execution_transition_policy") or {})).get(
                                    "applied_reason_codes", []
                                )
                                or []
                            )
                            if str(x)
                        ]
                        + [str(x) for x in list(pilot_runtime_reasons or []) if str(x)]
                    )
                )
                resp.diagnostics["assistant_execution_receipt"] = _build_execution_receipt_stub(
                    handshake_bundle=handshake,
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    workspace_id=str(workspace_id or ""),
                    request_id=str(get_request_id(http) or ""),
                    executed_action_ids=executed_action_ids,
                )
                resp.diagnostics["execution_gateway_contract_version"] = EXECUTION_GATEWAY_CONTRACT_VERSION
                resp.diagnostics["assistant_execution_gateway"] = _build_safe_mode_execution_gateway(
                    handshake_bundle=handshake,
                    receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["execution_pilot_contract_version"] = EXECUTION_PILOT_CONTRACT_VERSION
                resp.diagnostics["assistant_execution_pilot"] = _build_execution_pilot_bundle(
                    handshake_bundle=handshake,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    receipt_bundle=dict(resp.diagnostics.get("assistant_execution_receipt") or {}),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["assistant_approval_session"] = _build_approval_session_bundle(
                    handshake_bundle=handshake,
                    plan_bundle=plan_bundle,
                    workspace_id=str(workspace_id or ""),
                    request_id=str(get_request_id(http) or ""),
                )
                resp.diagnostics["durable_approval_session_contract_version"] = DURABLE_APPROVAL_SESSION_CONTRACT_VERSION
                resp.diagnostics["assistant_durable_approval_session"] = _build_durable_approval_session_record(
                    approval_session_bundle=dict(resp.diagnostics.get("assistant_approval_session") or {}),
                    session_id=str(getattr(req, "session_id", "") or "default"),
                    confirmation_token=str(handshake.get("confirmation_token", "") or ""),
                    transition_input=transition_input,
                    previous_record=loaded_durable_approval,
                )
                resp.diagnostics["idempotency_record_contract_version"] = IDEMPOTENCY_RECORD_CONTRACT_VERSION
                resp.diagnostics["assistant_idempotency_record"] = _build_idempotency_record_snapshot(
                    execution_idempotency_bundle=execution_idempotency,
                    workspace_id=str(workspace_id or ""),
                    plan_id=str(plan_bundle.get("plan_id", "") or ""),
                    transition_input=transition_input,
                )
        except Exception:
            pass

        try:
            resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
            _hydrate_durable_records_into_diagnostics(
                diagnostics=resp.diagnostics,
                loaded_approval=loaded_durable_approval,
                loaded_idempotency=loaded_durable_idempotency,
            )
        except Exception:
            pass

        try:
            await _persist_durable_records(
                req=req,
                resp=resp,
                workspace_id=workspace_id,
                get_memory_store=get_memory_store,
            )
        except Exception:
            pass

        await _save_session_memory(
            req=req,
            resp=resp,
            workspace_id=workspace_id,
            get_memory_store=get_memory_store,
        )

        return resp
