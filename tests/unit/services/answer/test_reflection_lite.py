from __future__ import annotations

from src.services.answer.classifier import QueryType
from src.services.answer.reflection_lite import apply_reflection_lite


class _Req:
    def __init__(self, query: str):
        self.query = query


class _Resp:
    def __init__(self, answer: str):
        self.answer = answer
        self.diagnostics = {"response_language": "ru", "planning_reason_codes": []}


def test_reflection_lite_rewrites_stub_once():
    req = _Req(query="Что ты умеешь?")
    resp = _Resp(answer="(reasoning layer stub)")
    out = apply_reflection_lite(resp=resp, req=req, query_type=QueryType.DIALOG, max_retries=1)
    assert "(reasoning layer stub)" not in str(out.answer)
    reflection = dict(getattr(out, "diagnostics", {}).get("reflection_lite") or {})
    assert reflection.get("retries_used") == 1
    assert reflection.get("rewrite_applied") is True
    assert "assistant_reflection_lite_retry_applied" in list(getattr(out, "diagnostics", {}).get("planning_reason_codes") or [])


def test_reflection_lite_skips_when_answer_is_ok():
    req = _Req(query="Привет")
    resp = _Resp(answer="Короткий полезный ответ по запросу.")
    out = apply_reflection_lite(resp=resp, req=req, query_type=QueryType.DIALOG, max_retries=1)
    assert out.answer == "Короткий полезный ответ по запросу."
    reflection = dict(getattr(out, "diagnostics", {}).get("reflection_lite") or {})
    assert reflection.get("retries_used") == 0
    assert reflection.get("rewrite_applied") is False

