from __future__ import annotations

import pytest

from src.services.answer import act_write_state_store as store


class _Mem:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], str] = {}

    async def get(self, *, workspace_id: str, key: str) -> str:
        return str(self.rows.get((workspace_id, key), ""))

    async def put(self, *, workspace_id: str, key: str, value: str, metadata: dict[str, object]) -> None:
        _ = metadata
        self.rows[(workspace_id, key)] = str(value)


@pytest.mark.asyncio
async def test_pending_confirmation_survives_cache_reset_via_memory_store(monkeypatch) -> None:
    mem = _Mem()
    monkeypatch.setattr("src.services.answer.act_write_state_store.get_memory_store", lambda: mem)
    scope = store.build_scope_key(session_id="s1", workspace_id="w1")
    payload = {"confirmation_token": "act-confirm:abc", "tool_name": "save_file", "consumed": False}
    await store.save_pending_confirmation(
        scope_key=scope,
        session_id="s1",
        workspace_id="w1",
        payload=payload,
    )
    store.reset_runtime_state_for_tests()
    loaded = await store.load_pending_confirmation(scope_key=scope, session_id="s1", workspace_id="w1")
    assert loaded.get("confirmation_token") == "act-confirm:abc"


@pytest.mark.asyncio
async def test_idempotency_record_survives_cache_reset_via_memory_store(monkeypatch) -> None:
    mem = _Mem()
    monkeypatch.setattr("src.services.answer.act_write_state_store.get_memory_store", lambda: mem)
    scope = store.build_scope_key(session_id="s2", workspace_id="w2")
    await store.save_idempotency_record(
        scope_key=scope,
        session_id="s2",
        workspace_id="w2",
        idempotency_key="id-1",
        payload={"confirmation_token": "act-confirm:def", "result": {"ok": True}},
    )
    store.reset_runtime_state_for_tests()
    loaded = await store.load_idempotency_record(
        scope_key=scope,
        session_id="s2",
        workspace_id="w2",
        idempotency_key="id-1",
    )
    assert loaded.get("confirmation_token") == "act-confirm:def"


@pytest.mark.asyncio
async def test_load_idempotency_record_ignores_expired_payload(monkeypatch) -> None:
    mem = _Mem()
    monkeypatch.setattr("src.services.answer.act_write_state_store.get_memory_store", lambda: mem)
    scope = store.build_scope_key(session_id="s3", workspace_id="w3")
    await store.save_idempotency_record(
        scope_key=scope,
        session_id="s3",
        workspace_id="w3",
        idempotency_key="id-expired",
        payload={"confirmation_token": "act-confirm:expired", "result": {"ok": True}},
        now_epoch=100,
        ttl_seconds=1,
    )
    loaded = await store.load_idempotency_record(
        scope_key=scope,
        session_id="s3",
        workspace_id="w3",
        idempotency_key="id-expired",
    )
    assert loaded == {}


@pytest.mark.asyncio
async def test_cleanup_expired_write_state_reports_metrics(monkeypatch) -> None:
    mem = _Mem()
    monkeypatch.setattr("src.services.answer.act_write_state_store.get_memory_store", lambda: mem)
    scope = store.build_scope_key(session_id="s4", workspace_id="w4")
    await store.save_pending_confirmation(
        scope_key=scope,
        session_id="s4",
        workspace_id="w4",
        payload={"confirmation_token": "act-confirm:old", "expires_at": 100, "tool_name": "save_file", "consumed": False},
    )
    await store.save_idempotency_record(
        scope_key=scope,
        session_id="s4",
        workspace_id="w4",
        idempotency_key="id-old",
        payload={"confirmation_token": "act-confirm:old", "result": {"ok": True}},
        now_epoch=100,
        ttl_seconds=1,
    )
    stats = await store.cleanup_expired_write_state(
        scope_key=scope,
        session_id="s4",
        workspace_id="w4",
        now_epoch=200,
    )
    assert int(stats.get("pending_expired", 0) or 0) == 1
    assert int(stats.get("idempotency_expired", 0) or 0) == 1
