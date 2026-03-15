from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.mode_router import apply_runtime_mode_diagnostics, resolve_answer_runtime_mode


class _Resp:
    def __init__(self) -> None:
        self.diagnostics = {}


def test_mode_router_falls_back_to_answer_when_act_disabled() -> None:
    req = AnswerRequest(query="check", filters={"runtime_mode": "act"})
    route = resolve_answer_runtime_mode(req=req, runtime_context={"assistant_actions_enabled": False})

    assert route["requested_mode"] == "act"
    assert route["selected_mode"] == "answer"
    assert "runtime_mode_act_disabled_fallback_answer" in list(route["reason_codes"] or [])


def test_mode_router_records_diagnostics_contract() -> None:
    resp = _Resp()
    apply_runtime_mode_diagnostics(
        resp=resp,
        route={"requested_mode": "act", "selected_mode": "answer", "reason_codes": ["x_reason"]},
    )
    runtime_mode = dict(resp.diagnostics.get("runtime_mode") or {})
    assert runtime_mode.get("requested_mode") == "act"
    assert runtime_mode.get("selected_mode") == "answer"
    assert list(runtime_mode.get("reason_codes") or []) == ["x_reason"]
