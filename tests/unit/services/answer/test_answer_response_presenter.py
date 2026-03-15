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
    assert dict(diagnostics.get("presentation") or {}).get("mode") == "full"


def test_response_presenter_compact_mode_excludes_verbose_diagnostics() -> None:
    resp = _Resp()
    req = AnswerRequest(query="q", filters={"response_presentation": "compact"})
    out = present_answer_response(req=req, resp=resp)
    diagnostics = dict(out.diagnostics or {})
    assert "planner_runtime_parity" not in diagnostics
    assert "tool_selection" not in diagnostics
    assert diagnostics.get("response_mode") == "strict_rag"
    assert dict(diagnostics.get("presentation") or {}).get("mode") == "compact"
