from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.services.answer.act_read_only import apply_act_read_only_runtime


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


@pytest.mark.asyncio
async def test_act_read_only_runtime_blocks_non_allowlisted_tool() -> None:
    req = AnswerRequest(query="x", filters={"act_tool_name": "save_file", "act_tool_args": {"path": "a.txt"}})
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
async def test_act_read_only_runtime_executes_list_files_when_allowlisted() -> None:
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
