from __future__ import annotations

from src.services.answer.classifier import QueryType


def _normalize_query_type(query_type: QueryType | str) -> str:
    if isinstance(query_type, QueryType):
        return str(query_type.value)
    value = str(query_type or "").strip().lower()
    return value if value in {"dialog", "advice", "action"} else "dialog"


def apply_tool_policy_route_contract(
    *,
    req: object,
    route: dict[str, object],
    query_type: QueryType | str,
) -> dict[str, object]:
    qtype = _normalize_query_type(query_type)
    resolved = dict(route or {})
    reason_codes: list[str] = ["tool_policy_route_contract_evaluated"]
    selected_mode = str(resolved.get("selected_mode", "answer") or "answer")
    filters = dict(getattr(req, "filters", None) or {})

    if qtype == "dialog" and selected_mode == "act":
        resolved["selected_mode"] = "answer"
        reason_codes.append("tool_policy_dialog_act_blocked")
    elif qtype == "action" and selected_mode == "act":
        idempotency_key = str(filters.get("act_idempotency_key", "") or "").strip()
        if not idempotency_key:
            resolved["selected_mode"] = "answer"
            reason_codes.append("tool_policy_action_idempotency_required")
        else:
            reason_codes.append("tool_policy_action_idempotency_present")
    else:
        reason_codes.append("tool_policy_route_unchanged")

    resolved["tool_policy_contract"] = {
        "contract_version": "v1",
        "query_type": qtype,
        "reason_codes": sorted(set(reason_codes)),
    }
    return resolved


def apply_tool_policy_response_contract(
    *,
    resp: object,
    query_type: QueryType | str,
) -> object:
    qtype = _normalize_query_type(query_type)
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    policy = dict(diagnostics.get("tool_policy_contract") or {})
    policy.setdefault("contract_version", "v1")
    policy["query_type"] = qtype
    reason_codes = list(policy.get("reason_codes") or [])
    reason_codes.append("tool_policy_response_contract_evaluated")

    if qtype == "advice":
        answer = str(getattr(resp, "answer", "") or "").strip()
        lowered = answer.lower()
        ru_mark = "это рекомендация"
        en_mark = "this is advisory guidance"
        if answer and ru_mark not in lowered and en_mark not in lowered:
            if any("\u0400" <= ch <= "\u04FF" for ch in answer):
                resp.answer = f"Это рекомендация (без авто-выполнения): {answer}"
            else:
                resp.answer = f"This is advisory guidance (no auto-execution): {answer}"
            reason_codes.append("tool_policy_advice_disclaimer_applied")
        else:
            reason_codes.append("tool_policy_advice_disclaimer_skipped")
    diagnostics["tool_policy_contract"] = {
        **policy,
        "reason_codes": sorted(set([str(x) for x in reason_codes if str(x)])),
    }
    setattr(resp, "diagnostics", diagnostics)
    return resp

