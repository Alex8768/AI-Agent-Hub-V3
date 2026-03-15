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
