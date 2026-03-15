"""Durable state helpers for Act write-confirm runtime."""

from __future__ import annotations

import json
import time
from typing import Any

from src.core.providers import get_memory_store


_PENDING_WRITE_CONFIRMATIONS: dict[str, dict[str, object]] = {}
_WRITE_CONFIRM_IDEMPOTENCY: dict[str, dict[str, object]] = {}
_IDEMPOTENCY_INDEX: dict[str, list[dict[str, object]]] = {}
_DECISION_RATE_EVENTS: dict[str, list[int]] = {}
_IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60
_MAX_PENDING_CONFIRMATIONS_PER_SESSION = 1
_MAX_IDEMPOTENCY_RECORDS_PER_SESSION = 128
_DECISION_RATE_WINDOW_SECONDS = 60
_MAX_DECISIONS_PER_WINDOW = 12


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


def _idempotency_index_store_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:act_write_idempotency_index"


def _decision_rate_store_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:act_write_decision_rate_events"


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


async def _load_json_list_record(*, workspace_id: str, key: str) -> list[dict[str, object]]:
    try:
        mem = get_memory_store()
        mem_get = getattr(mem, "get", None)
        if not callable(mem_get):
            return []
        raw = await mem_get(workspace_id=str(workspace_id or ""), key=str(key or ""))
        parsed = json.loads(str(raw or ""))
        if not isinstance(parsed, list):
            return []
        return [dict(row or {}) for row in parsed if isinstance(row, dict)]
    except Exception:
        return []


async def _save_json_list_record(*, workspace_id: str, key: str, payload: list[dict[str, object]], metadata: dict[str, object]) -> None:
    try:
        mem = get_memory_store()
        mem_put = getattr(mem, "put", None)
        if not callable(mem_put):
            return
        await mem_put(
            workspace_id=str(workspace_id or ""),
            key=str(key or ""),
            value=json.dumps([dict(row or {}) for row in payload], ensure_ascii=True, sort_keys=True),
            metadata=dict(metadata or {}),
        )
    except Exception:
        return


async def _load_epoch_list_record(*, workspace_id: str, key: str) -> list[int]:
    try:
        mem = get_memory_store()
        mem_get = getattr(mem, "get", None)
        if not callable(mem_get):
            return []
        raw = await mem_get(workspace_id=str(workspace_id or ""), key=str(key or ""))
        parsed = json.loads(str(raw or ""))
        if not isinstance(parsed, list):
            return []
        return [int(item or 0) for item in parsed if isinstance(item, int | float)]
    except Exception:
        return []


async def _save_epoch_list_record(*, workspace_id: str, key: str, payload: list[int], metadata: dict[str, object]) -> None:
    try:
        mem = get_memory_store()
        mem_put = getattr(mem, "put", None)
        if not callable(mem_put):
            return
        await mem_put(
            workspace_id=str(workspace_id or ""),
            key=str(key or ""),
            value=json.dumps([int(item or 0) for item in payload], ensure_ascii=True, sort_keys=True),
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


async def _load_idempotency_index(*, scope_key: str, session_id: str, workspace_id: str) -> list[dict[str, object]]:
    cached = list(_IDEMPOTENCY_INDEX.get(scope_key) or [])
    if cached:
        return [dict(row or {}) for row in cached]
    rows = await _load_json_list_record(workspace_id=workspace_id, key=_idempotency_index_store_key(session_id=session_id))
    if rows:
        _IDEMPOTENCY_INDEX[scope_key] = [dict(row or {}) for row in rows]
    return [dict(row or {}) for row in rows]


async def _save_idempotency_index(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    rows: list[dict[str, object]],
) -> None:
    normalized = [dict(row or {}) for row in rows if str(dict(row or {}).get("idempotency_key", "")).strip()]
    _IDEMPOTENCY_INDEX[scope_key] = normalized
    await _save_json_list_record(
        workspace_id=workspace_id,
        key=_idempotency_index_store_key(session_id=session_id),
        payload=normalized,
        metadata={"session_id": str(session_id or "default"), "kind": "act_write_idempotency_index"},
    )


async def load_idempotency_record(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    cache_key = f"{scope_key}:{str(idempotency_key or '').strip()}"
    now_epoch = int(time.time())
    record = dict(_WRITE_CONFIRM_IDEMPOTENCY.get(cache_key) or {})
    if record:
        expires_at = int(record.get("expires_at", 0) or 0)
        if expires_at and now_epoch > expires_at:
            _WRITE_CONFIRM_IDEMPOTENCY.pop(cache_key, None)
            return {}
        return record
    record = await _load_json_record(
        workspace_id=workspace_id,
        key=_idempotency_store_key(session_id=session_id, idempotency_key=idempotency_key),
    )
    expires_at = int(record.get("expires_at", 0) or 0) if record else 0
    if record and expires_at and now_epoch > expires_at:
        _WRITE_CONFIRM_IDEMPOTENCY.pop(cache_key, None)
        return {}
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
    now_epoch: int | None = None,
    ttl_seconds: int = _IDEMPOTENCY_TTL_SECONDS,
) -> None:
    normalized_key = str(idempotency_key or "").strip()
    cache_key = f"{scope_key}:{normalized_key}"
    now_value = int(now_epoch if isinstance(now_epoch, int) else time.time())
    expires_at = int(now_value + max(int(ttl_seconds or 0), 0))
    row = dict(payload or {})
    row.setdefault("idempotency_key", normalized_key)
    row.setdefault("created_at", now_value)
    row.setdefault("expires_at", expires_at)
    _WRITE_CONFIRM_IDEMPOTENCY[cache_key] = row
    await _save_json_record(
        workspace_id=workspace_id,
        key=_idempotency_store_key(session_id=session_id, idempotency_key=normalized_key),
        payload=row,
        metadata={"session_id": str(session_id or "default"), "kind": "act_write_idempotency_record"},
    )
    index_rows = await _load_idempotency_index(scope_key=scope_key, session_id=session_id, workspace_id=workspace_id)
    filtered = [dict(item or {}) for item in index_rows if str(dict(item or {}).get("idempotency_key", "")).strip() != normalized_key]
    filtered.append({"idempotency_key": normalized_key, "expires_at": expires_at})
    await _save_idempotency_index(
        scope_key=scope_key,
        session_id=session_id,
        workspace_id=workspace_id,
        rows=filtered,
    )


async def cleanup_expired_write_state(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    now_epoch: int | None = None,
) -> dict[str, object]:
    now_value = int(now_epoch if isinstance(now_epoch, int) else time.time())
    pending_expired = 0
    idempotency_expired = 0

    pending = await load_pending_confirmation(scope_key=scope_key, session_id=session_id, workspace_id=workspace_id)
    pending_expires_at = int(pending.get("expires_at", 0) or 0) if pending else 0
    if pending and pending_expires_at and now_value > pending_expires_at:
        await save_pending_confirmation(
            scope_key=scope_key,
            session_id=session_id,
            workspace_id=workspace_id,
            payload={},
        )
        pending_expired = 1

    index_rows = await _load_idempotency_index(scope_key=scope_key, session_id=session_id, workspace_id=workspace_id)
    next_rows: list[dict[str, object]] = []
    for row in index_rows:
        item = dict(row or {})
        key = str(item.get("idempotency_key", "") or "").strip()
        if not key:
            continue
        expires_at = int(item.get("expires_at", 0) or 0)
        if expires_at and now_value > expires_at:
            _WRITE_CONFIRM_IDEMPOTENCY.pop(f"{scope_key}:{key}", None)
            idempotency_expired += 1
            continue
        next_rows.append({"idempotency_key": key, "expires_at": expires_at})
    if len(next_rows) != len(index_rows):
        await _save_idempotency_index(
            scope_key=scope_key,
            session_id=session_id,
            workspace_id=workspace_id,
            rows=next_rows,
        )
    return {
        "pending_expired": pending_expired,
        "idempotency_expired": idempotency_expired,
        "idempotency_index_size": len(next_rows),
    }


def _trim_rate_events(*, events: list[int], now_epoch: int, window_seconds: int) -> list[int]:
    threshold = int(now_epoch - max(int(window_seconds or 0), 0))
    return [int(ts or 0) for ts in list(events or []) if int(ts or 0) >= threshold]


async def evaluate_pending_confirmation_quota(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    now_epoch: int | None = None,
    max_pending: int = _MAX_PENDING_CONFIRMATIONS_PER_SESSION,
) -> dict[str, object]:
    now_value = int(now_epoch if isinstance(now_epoch, int) else time.time())
    pending = await load_pending_confirmation(scope_key=scope_key, session_id=session_id, workspace_id=workspace_id)
    expires_at = int(pending.get("expires_at", 0) or 0) if pending else 0
    consumed = bool(pending.get("consumed", False)) if pending else False
    is_open_pending = bool(pending) and not consumed and (not expires_at or now_value <= expires_at)
    active_count = 1 if is_open_pending else 0
    limit = max(int(max_pending or 0), 0)
    blocked = active_count >= limit if limit else False
    return {
        "allowed": not blocked,
        "reason_code": "act_write_pending_quota_exceeded" if blocked else "",
        "active_pending": active_count,
        "max_pending": limit,
    }


async def evaluate_idempotency_quota(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    now_epoch: int | None = None,
    idempotency_key: str = "",
    max_records: int = _MAX_IDEMPOTENCY_RECORDS_PER_SESSION,
) -> dict[str, object]:
    now_value = int(now_epoch if isinstance(now_epoch, int) else time.time())
    rows = await _load_idempotency_index(scope_key=scope_key, session_id=session_id, workspace_id=workspace_id)
    next_rows: list[dict[str, object]] = []
    for row in rows:
        item = dict(row or {})
        key = str(item.get("idempotency_key", "") or "").strip()
        if not key:
            continue
        expires_at = int(item.get("expires_at", 0) or 0)
        if expires_at and now_value > expires_at:
            continue
        next_rows.append({"idempotency_key": key, "expires_at": expires_at})
    if len(next_rows) != len(rows):
        await _save_idempotency_index(
            scope_key=scope_key,
            session_id=session_id,
            workspace_id=workspace_id,
            rows=next_rows,
        )
    normalized_key = str(idempotency_key or "").strip()
    existing_keys = {str(item.get("idempotency_key", "") or "").strip() for item in next_rows}
    active_count = len(existing_keys)
    limit = max(int(max_records or 0), 0)
    blocked = bool(limit and active_count >= limit and normalized_key and normalized_key not in existing_keys)
    return {
        "allowed": not blocked,
        "reason_code": "act_write_idempotency_quota_exceeded" if blocked else "",
        "active_records": active_count,
        "max_records": limit,
    }


async def evaluate_decision_rate_limit(
    *,
    scope_key: str,
    session_id: str,
    workspace_id: str,
    now_epoch: int | None = None,
    record_event: bool = True,
    max_events: int = _MAX_DECISIONS_PER_WINDOW,
    window_seconds: int = _DECISION_RATE_WINDOW_SECONDS,
) -> dict[str, object]:
    now_value = int(now_epoch if isinstance(now_epoch, int) else time.time())
    cache_key = str(scope_key or "default")
    events = list(_DECISION_RATE_EVENTS.get(cache_key) or [])
    if not events:
        events = await _load_epoch_list_record(
            workspace_id=workspace_id,
            key=_decision_rate_store_key(session_id=session_id),
        )
    pruned = _trim_rate_events(events=events, now_epoch=now_value, window_seconds=window_seconds)
    limit = max(int(max_events or 0), 0)
    blocked = bool(limit and len(pruned) >= limit)
    if not blocked and record_event:
        pruned.append(now_value)
    _DECISION_RATE_EVENTS[cache_key] = list(pruned)
    await _save_epoch_list_record(
        workspace_id=workspace_id,
        key=_decision_rate_store_key(session_id=session_id),
        payload=pruned,
        metadata={"session_id": str(session_id or "default"), "kind": "act_write_decision_rate_events"},
    )
    return {
        "allowed": not blocked,
        "reason_code": "act_write_decision_rate_limited" if blocked else "",
        "events_in_window": len(pruned),
        "max_events": limit,
        "window_seconds": int(window_seconds or 0),
    }


def reset_runtime_state_for_tests() -> None:
    _PENDING_WRITE_CONFIRMATIONS.clear()
    _WRITE_CONFIRM_IDEMPOTENCY.clear()
    _IDEMPOTENCY_INDEX.clear()
    _DECISION_RATE_EVENTS.clear()
