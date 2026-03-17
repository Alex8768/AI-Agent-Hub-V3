from __future__ import annotations

from src.services.answer.classifier import QueryType
from src.services.answer.context.memory_lite import (
    apply_memory_lite_runtime_diagnostics,
    attach_memory_lite_context,
)


class _Req:
    session_id = "sess-1"
    session_memory_last_answer = "Предыдущий ответ про структуру презентации и вывод."


class _Resp:
    def __init__(self):
        self.diagnostics = {}


def test_attach_memory_lite_context_uses_session_memory():
    req = _Req()
    context = attach_memory_lite_context(req=req, query_type=QueryType.ADVICE)
    assert context["mode"] == "session_context_first"
    assert context["query_type"] == "advice"
    assert context["has_last_answer"] is True
    assert "структуру презентации" in str(context["last_answer_excerpt"]).lower()


def test_apply_memory_lite_runtime_diagnostics_sets_payload():
    req = _Req()
    resp = _Resp()
    out = apply_memory_lite_runtime_diagnostics(
        resp=resp,
        req=req,
        query_type=QueryType.DIALOG,
    )
    diagnostics = dict(getattr(out, "diagnostics", {}) or {})
    payload = dict(diagnostics.get("memory_lite") or {})
    assert payload["contract_version"] == "v1"
    assert payload["query_type"] == "dialog"
    assert "memory_lite_context_attached" in list(payload.get("reason_codes") or [])

