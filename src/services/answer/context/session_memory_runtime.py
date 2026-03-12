from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.context.session_text import clip_text as _clip_text


async def load_session_memory(
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


async def save_session_memory(
    *,
    req: AnswerRequest,
    resp: Any,
    workspace_id: str,
    get_memory_store: object,
    logger: object,
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
        except Exception as fallback_exc:
            logger.warning(
                "Answer service soft-failure: session memory failure diagnostics skipped",
                context={
                    "workspace_id": str(workspace_id or ""),
                    "error": str(fallback_exc),
                    "error_type": type(fallback_exc).__name__,
                    "reason_code": "answer_service_session_memory_diagnostics_soft_failure",
                },
            )
