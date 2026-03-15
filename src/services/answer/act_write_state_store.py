"""Durable state helpers for Act write-confirm runtime."""

from __future__ import annotations

import json
from typing import Any

from src.core.providers import get_memory_store


_PENDING_WRITE_CONFIRMATIONS: dict[str, dict[str, object]] = {}
_WRITE_CONFIRM_IDEMPOTENCY: dict[str, dict[str, object]] = {}


def build_scope_key(*, session_id: str, workspace_id: str) -> str:
    sid = str(session_id or "default")
    wid = str(workspace_id or "default")
    return f"{wid}:{sid}"


def _pending_store_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:act_write_pending_confirmation"


def _idempotency_store_key(*, session_id: str, idempotency_key: str) -> str:
    sid = str(session_id or "default")
    key = str(idempotency_key or "").strip() or "missing"
    return f"session:{sid}:act_write_idempotency:{key}"


async def _load_json_record(*, workspace_id: str, key: str) -> dict[str, object]:
    try:
        mem = get_memory_store()
        mem_get = getattr(mem, "get", None)
        if not callable(mem_get):
            return {}
        raw = await mem_get(workspace_id=str(workspace_id or ""), key=str(key or ""))
        return dict(json.loads(str(raw or "")) or {})
    except Exception:
        return {}


async def _save_json_record(*, workspace_id: str, key: str, payload: dict[str, object], metadata: dict[str, object]) -> None:
    try:
        mem = get_memory_store()
        mem_put = getattr(mem, "put", None)
        if not callable(mem_put):
            return
        await mem_put(
            workspace_id=str(workspace_id or ""),
            key=str(key or ""),
            value=json.dumps(dict(payload or {}), ensure_ascii=True, sort_keys=True),
            metadata=dict(metadata or {}),
        )
    except Exception:
        return


async def load_pending_confirmation(*, scope_key: str, session_id: str, workspace_id: str) -> dict[str, object]:
    pending = dict(_PENDING_WRITE_CONFIRMATIONS.get(scope_key) or {})
    if pending:
        return pending
    pending = await _load_json_record(workspace_id=workspace_id, key=_pending_store_key(session_id=session_id))
    if pending:
        _PENDING_WRITE_CONFIRMATIONS[scope_key] = dict(pending)
    return dict(pending)


async def save_pending_confirmation(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    payload: dict[str, object],
) -> None:
    pending = dict(payload or {})
    _PENDING_WRITE_CONFIRMATIONS[scope_key] = pending
    await _save_json_record(
        workspace_id=workspace_id,
        key=_pending_store_key(session_id=session_id),
        payload=pending,
        metadata={"session_id": str(session_id or "default"), "kind": "act_write_pending_confirmation"},
    )


async def load_idempotency_record(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    cache_key = f"{scope_key}:{str(idempotency_key or '').strip()}"
    record = dict(_WRITE_CONFIRM_IDEMPOTENCY.get(cache_key) or {})
    if record:
        return record
    record = await _load_json_record(
        workspace_id=workspace_id,
        key=_idempotency_store_key(session_id=session_id, idempotency_key=idempotency_key),
    )
    if record:
        _WRITE_CONFIRM_IDEMPOTENCY[cache_key] = dict(record)
    return dict(record)


async def save_idempotency_record(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    idempotency_key: str,
    payload: dict[str, object],
) -> None:
    cache_key = f"{scope_key}:{str(idempotency_key or '').strip()}"
    row = dict(payload or {})
    _WRITE_CONFIRM_IDEMPOTENCY[cache_key] = row
    await _save_json_record(
        workspace_id=workspace_id,
        key=_idempotency_store_key(session_id=session_id, idempotency_key=idempotency_key),
        payload=row,
        metadata={"session_id": str(session_id or "default"), "kind": "act_write_idempotency_record"},
    )


def reset_runtime_state_for_tests() -> None:
    _PENDING_WRITE_CONFIRMATIONS.clear()
    _WRITE_CONFIRM_IDEMPOTENCY.clear()
