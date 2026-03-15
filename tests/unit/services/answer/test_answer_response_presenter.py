from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.response_presenter import present_answer_response


class _Resp:
    def __init__(self) -> None:
        self.diagnostics = {
            "planner_runtime_parity": {"status": "ok"},
            "tool_selection": {"status": "ok"},
            "response_mode": "strict_rag",
        }


def test_response_presenter_keeps_full_diagnostics_by_default() -> None:
    resp = _Resp()
    req = AnswerRequest(query="q")
    out = present_answer_response(req=req, resp=resp)
    diagnostics = dict(out.diagnostics or {})
    assert "planner_runtime_parity" in diagnostics
    presentation = dict(diagnostics.get("presentation") or {})
    assert presentation.get("mode") == "full"
    assert presentation.get("requested_mode") == "full"
    assert list(presentation.get("reason_codes") or []) == []


def test_response_presenter_compact_mode_excludes_verbose_diagnostics() -> None:
    resp = _Resp()
    req = AnswerRequest(query="q", filters={"response_presentation": "compact"})
    out = present_answer_response(req=req, resp=resp)
    diagnostics = dict(out.diagnostics or {})
    assert "planner_runtime_parity" not in diagnostics
    assert "tool_selection" not in diagnostics
    assert diagnostics.get("response_mode") == "strict_rag"
    presentation = dict(diagnostics.get("presentation") or {})
    assert presentation.get("mode") == "compact"
    assert presentation.get("requested_mode") == "compact"


def test_response_presenter_supports_expanded_alias() -> None:
    resp = _Resp()
    req = AnswerRequest(query="q", filters={"diagnostics_view": "expanded"})
    out = present_answer_response(req=req, resp=resp)
    diagnostics = dict(out.diagnostics or {})
    presentation = dict(diagnostics.get("presentation") or {})
    assert presentation.get("mode") == "full"
    assert "diagnostics_view_alias_expanded_to_full" in list(presentation.get("reason_codes") or [])
