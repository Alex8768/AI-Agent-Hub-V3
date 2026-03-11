from __future__ import annotations

from typing import Any

from src.layers.pro.anticipatory.scanner import OpportunityScanner
from src.layers.pro.anticipatory.suggestions import build_proactive_suggestion_bundle
from src.layers.pro.anticipatory.whisper import WhisperRunner


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


async def run_answer_anticipatory_safe_mode(
    *,
    req: object,
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
