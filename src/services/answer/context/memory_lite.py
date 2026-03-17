from __future__ import annotations

from src.services.answer.classifier import QueryType
from src.services.answer.context.session_text import clip_text as _clip_text


def _normalize_query_type(query_type: QueryType | str) -> str:
    if isinstance(query_type, QueryType):
        return str(query_type.value)
    value = str(query_type or "").strip().lower()
    return value if value in {"dialog", "advice", "action"} else "dialog"


def attach_memory_lite_context(*, req: object, query_type: QueryType | str) -> dict[str, object]:
    session_id = str(getattr(req, "session_id", "") or "default")
    last_answer = _clip_text(getattr(req, "session_memory_last_answer", "") or "")
    context = {
        "contract_version": "v1",
        "mode": "session_context_first",
        "session_id": session_id,
        "query_type": _normalize_query_type(query_type),
        "has_last_answer": bool(last_answer),
        "last_answer_excerpt": _clip_text(last_answer)[:240],
    }
    return context


def apply_memory_lite_runtime_diagnostics(
    *,
    resp: object,
    req: object,
    query_type: QueryType | str,
    context: dict[str, object] | None = None,
) -> object:
    payload_context = dict(context or {})
    if not payload_context:
        payload_context = attach_memory_lite_context(req=req, query_type=query_type)
    reason_codes = ["memory_lite_context_attached"]
    if bool(payload_context.get("has_last_answer", False)):
        reason_codes.append("memory_lite_session_hit")
    else:
        reason_codes.append("memory_lite_session_miss")
    payload = {
        **payload_context,
        "reason_codes": sorted(set(reason_codes)),
    }
    diagnostics = dict(getattr(resp, "diagnostics", None) or {})
    diagnostics.setdefault("memory_lite", payload)
    setattr(resp, "diagnostics", diagnostics)
    return resp

