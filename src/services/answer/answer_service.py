from __future__ import annotations

import hashlib
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
    AnswerRequest,
    EVIDENCE_CONTRACT_VERSION,
    HANDSHAKE_CONTRACT_VERSION,
    INTENT_CONTRACT_VERSION,
    PLAN_CONTRACT_VERSION,
    SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN,
    SELF_CHECK_MISSING_MINIMAL_COUNT_MAX,
    VERIFY_DIAGNOSTICS_VERSION,
    VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED,
    VERIFY_SELF_CHECK_REASONS_COUNT_MAX,
    VERIFY_SELF_CHECK_STATUS_REQUIRED,
)
from src.observability.request_context import get_request_id

SESSION_MEMORY_MAX_CHARS = 4000


def _clip_text(value: object, *, max_chars: int = SESSION_MEMORY_MAX_CHARS) -> str:
    text = str(value or "")
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _detect_response_language(query: str) -> str:
    text = str(query or "")
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    return "en"


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


def _apply_diagnostics(
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
        plan = _build_deterministic_plan(
            query=str(getattr(req, "query", "") or ""),
            intent_payload=intent,
            assistant_mode_enabled=assistant_mode_enabled,
        )
        plan, planning_policy = _apply_plan_policy_guards(plan_bundle=plan, max_steps=5)
        diag.setdefault("plan_contract_version", PLAN_CONTRACT_VERSION)
        diag.setdefault("assistant_plan", dict(plan))
        diag.setdefault("planning_policy", dict(planning_policy))
        anticipatory = dict(diag.get("anticipatory") or {})
        draft_actions = dict(anticipatory.get("draft_actions") or {})
        handshake = _build_execution_handshake_bundle(
            plan_bundle=plan,
            draft_actions_bundle=draft_actions,
            assistant_mode_enabled=assistant_mode_enabled,
            actions_enabled=assistant_actions_enabled,
        )
        diag.setdefault("execution_handshake_contract_version", HANDSHAKE_CONTRACT_VERSION)
        diag.setdefault("assistant_execution_handshake", handshake)
        reason_codes = list(intent.get("reason_codes") or []) + list(plan.get("reason_codes") or [])
        reason_codes.extend(list(planning_policy.get("reason_codes") or []))
        reason_codes.extend(list(handshake.get("reason_codes") or []))
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
        _apply_diagnostics(
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
                anticipatory["draft_actions"] = _bridge_plan_to_draft_actions(
                    plan_bundle=dict(diag.get("assistant_plan") or {}),
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics = dict(getattr(resp, "diagnostics", None) or {})
                resp.diagnostics["anticipatory"] = anticipatory
                plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
                resp.diagnostics["assistant_execution_handshake"] = _build_execution_handshake_bundle(
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(anticipatory.get("draft_actions") or {}),
                    assistant_mode_enabled=assistant_mode_enabled,
                    actions_enabled=assistant_actions_enabled,
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
                base["draft_actions"] = _bridge_plan_to_draft_actions(
                    plan_bundle=dict(diag.get("assistant_plan") or {}),
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    language=str(assistant_response_language or "auto"),
                    actions_enabled=assistant_actions_enabled,
                )
                resp.diagnostics["anticipatory"] = base
                plan_bundle = dict(resp.diagnostics.get("assistant_plan") or {})
                resp.diagnostics["assistant_execution_handshake"] = _build_execution_handshake_bundle(
                    plan_bundle=plan_bundle,
                    draft_actions_bundle=dict(base.get("draft_actions") or {}),
                    assistant_mode_enabled=assistant_mode_enabled,
                    actions_enabled=assistant_actions_enabled,
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
