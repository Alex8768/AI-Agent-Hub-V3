from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.act_read_only import (
    _reset_act_write_runtime_state_for_tests,
    apply_act_read_only_runtime,
)
from src.services.answer import act_write_state_store


class _Resp:
    def __init__(self) -> None:
        self.diagnostics = {}


class _State:
    def __init__(self, invoker: object) -> None:
        self.mcp_tool_invoker = invoker


class _App:
    def __init__(self, invoker: object) -> None:
        self.state = _State(invoker)


class _HTTP:
    def __init__(self, invoker: object) -> None:
        self.app = _App(invoker)


class _Mem:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], str] = {}

    async def get(self, *, workspace_id: str, key: str) -> str:
        return str(self.rows.get((workspace_id, key), ""))

    async def put(self, *, workspace_id: str, key: str, value: str, metadata: dict[str, object]) -> None:
        _ = metadata
        self.rows[(workspace_id, key)] = str(value)


@pytest.mark.asyncio
async def test_act_read_only_runtime_blocks_non_allowlisted_tool(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()

    class _S:
        debug = True

    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())
    req = AnswerRequest(query="x", filters={"act_tool_name": "delete_file", "act_tool_args": {"path": "a.txt"}})
    resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=req,
        http=_HTTP(invoker=None),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "blocked"
    assert "act_read_only_tool_not_allowlisted" in list(diag.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_act_read_only_runtime_executes_list_files_when_allowlisted(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()

    class _S:
        debug = True

    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())

    async def _invoker(*, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        assert tool_name == "list_files"
        assert arguments == {"path": "."}
        return {"items": [{"path": "README.md", "type": "file"}], "count": 1}

    req = AnswerRequest(query="x", filters={"act_tool_name": "list_files", "act_tool_args": {"path": "."}})
    resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=req,
        http=_HTTP(invoker=_invoker),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "executed"
    assert diag.get("tool_name") == "list_files"
    assert "act_read_only_tool_executed" in list(diag.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_act_read_only_runtime_blocks_on_prod_strict_profile(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()

    class _S:
        debug = False

    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())
    req = AnswerRequest(query="x", filters={"act_tool_name": "list_files", "act_tool_args": {"path": "."}})
    resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=req,
        http=_HTTP(invoker=None),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "blocked"
    assert "act_blocked_by_policy_profile" in list(diag.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_act_write_runtime_requires_confirmation_in_dev_guided(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()

    class _S:
        debug = True

    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())
    req = AnswerRequest(query="x", filters={"act_tool_name": "save_file", "act_tool_args": {"path": "a.txt", "content": "hi"}})
    resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=req,
        http=_HTTP(invoker=None),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "pending_confirmation"
    assert "act_write_confirmation_required" in list(diag.get("reason_codes") or [])
    confirmation = dict(diag.get("confirmation") or {})
    assert str(confirmation.get("token", "")).startswith("act-confirm:")


@pytest.mark.asyncio
async def test_act_write_runtime_executes_after_approve(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()

    class _S:
        debug = True

    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())

    seen: dict[str, object] = {}

    async def _invoker(*, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        seen["tool_name"] = tool_name
        seen["arguments"] = dict(arguments)
        return {"ok": True}

    open_req = AnswerRequest(
        query="x",
        session_id="s1",
        filters={"act_tool_name": "save_file", "act_tool_args": {"path": "a.txt", "content": "v1"}},
    )
    open_resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=open_req,
        http=_HTTP(invoker=_invoker),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    token = str(dict(open_resp.diagnostics.get("act_runtime") or {}).get("confirmation", {}).get("token", ""))

    approve_req = AnswerRequest(
        query="x",
        session_id="s1",
        filters={
            "act_tool_name": "save_file",
            "act_confirm_decision": "approve",
            "act_confirmation_token": token,
            "act_idempotency_key": "id-1",
        },
    )
    approve_resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=approve_req,
        http=_HTTP(invoker=_invoker),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(approve_resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "executed"
    assert seen.get("tool_name") == "save_file"
    assert "act_write_tool_executed_confirmed" in list(diag.get("reason_codes") or [])


@pytest.mark.asyncio
async def test_act_write_runtime_restores_pending_state_from_durable_store(monkeypatch) -> None:
    _reset_act_write_runtime_state_for_tests()
    act_write_state_store.reset_runtime_state_for_tests()

    class _S:
        debug = True

    mem = _Mem()
    monkeypatch.setattr("src.services.answer.act_read_only.get_settings", lambda: _S())
    monkeypatch.setattr("src.services.answer.act_write_state_store.get_memory_store", lambda: mem)

    seen: dict[str, object] = {}

    async def _invoker(*, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        seen["tool_name"] = tool_name
        seen["arguments"] = dict(arguments)
        return {"ok": True}

    open_req = AnswerRequest(
        query="x",
        session_id="persist",
        filters={"act_tool_name": "save_file", "act_tool_args": {"path": "a.txt", "content": "v1"}},
    )
    open_resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=open_req,
        http=_HTTP(invoker=_invoker),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    token = str(dict(open_resp.diagnostics.get("act_runtime") or {}).get("confirmation", {}).get("token", ""))

    # Simulate process-local cache loss; durable store should still provide pending record.
    _reset_act_write_runtime_state_for_tests()
    act_write_state_store.reset_runtime_state_for_tests()

    approve_req = AnswerRequest(
        query="x",
        session_id="persist",
        filters={
            "act_tool_name": "save_file",
            "act_confirm_decision": "approve",
            "act_confirmation_token": token,
            "act_idempotency_key": "id-persist",
        },
    )
    approve_resp = await apply_act_read_only_runtime(
        resp=_Resp(),
        req=approve_req,
        http=_HTTP(invoker=_invoker),
        workspace_id="default",
        route={"selected_mode": "act"},
    )
    diag = dict(approve_resp.diagnostics.get("act_runtime") or {})
    assert diag.get("status") == "executed"
    assert seen.get("tool_name") == "save_file"
