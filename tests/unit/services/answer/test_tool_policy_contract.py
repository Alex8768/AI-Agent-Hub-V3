from __future__ import annotations

from src.services.answer.classifier import QueryType
from src.services.answer.tool_policy_contract import (
    apply_tool_policy_response_contract,
    apply_tool_policy_route_contract,
)


class _Req:
    def __init__(self, filters: dict[str, object] | None = None):
        self.filters = dict(filters or {})


class _Resp:
    def __init__(self, answer: str):
        self.answer = answer
        self.diagnostics = {}


def test_tool_policy_dialog_blocks_act_route():
    req = _Req(filters={"mode": "act"})
    route = {"selected_mode": "act"}
    resolved = apply_tool_policy_route_contract(req=req, route=route, query_type=QueryType.DIALOG)
    assert resolved["selected_mode"] == "answer"
    payload = dict(resolved.get("tool_policy_contract") or {})
    assert "tool_policy_dialog_act_blocked" in list(payload.get("reason_codes") or [])


def test_tool_policy_action_requires_idempotency_for_act():
    req = _Req(filters={"mode": "act"})
    route = {"selected_mode": "act"}
    resolved = apply_tool_policy_route_contract(req=req, route=route, query_type=QueryType.ACTION)
    assert resolved["selected_mode"] == "answer"
    payload = dict(resolved.get("tool_policy_contract") or {})
    assert "tool_policy_action_idempotency_required" in list(payload.get("reason_codes") or [])


def test_tool_policy_action_keeps_act_when_idempotency_present():
    req = _Req(filters={"mode": "act", "act_idempotency_key": "idem-1"})
    route = {"selected_mode": "act"}
    resolved = apply_tool_policy_route_contract(req=req, route=route, query_type=QueryType.ACTION)
    assert resolved["selected_mode"] == "act"


def test_tool_policy_advice_adds_disclaimer():
    resp = _Resp(answer="Сделай так: сначала собери требования, потом шаги.")
    out = apply_tool_policy_response_contract(resp=resp, query_type=QueryType.ADVICE)
    assert str(out.answer).lower().startswith("это рекомендация")
    payload = dict(getattr(out, "diagnostics", {}).get("tool_policy_contract") or {})
    assert "tool_policy_advice_disclaimer_applied" in list(payload.get("reason_codes") or [])

