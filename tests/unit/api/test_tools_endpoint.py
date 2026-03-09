from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import get_settings
from src.mcp_protocol import MCPToolRegistry


def test_tools_endpoint_returns_404_when_feature_disabled(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", False, raising=False)
    client = TestClient(app)
    response = client.get("/api/v1/tools")
    assert response.status_code == 404


def test_tools_endpoint_list_and_get_contract(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    registry = MCPToolRegistry()
    registry.register_server(
        {
            "server_name": "filesystem",
            "transport": "stdio",
            "endpoint": "",
            "enabled": True,
        }
    )
    registry.register_tool(
        {
            "tool_name": "read_file",
            "server_name": "filesystem",
            "description": "Read a file",
            "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
            "tags": ["filesystem"],
            "enabled": True,
        }
    )
    app.state.mcp_registry = registry

    client = TestClient(app)
    listed = client.get("/api/v1/tools")
    assert listed.status_code == 200
    payload = listed.json()
    assert set(payload.keys()) == {"tools", "servers", "total_tools", "total_servers"}
    assert payload["total_tools"] == 1
    assert payload["total_servers"] == 1
    assert payload["tools"][0]["tool_name"] == "read_file"
    assert payload["servers"][0]["server_name"] == "filesystem"

    one = client.get("/api/v1/tools/read_file")
    assert one.status_code == 200
    item = one.json()
    assert set(item.keys()) == {
        "tool_name",
        "server_name",
        "description",
        "input_schema",
        "tags",
        "enabled",
    }
    assert item["tool_name"] == "read_file"


def test_tools_endpoint_returns_404_for_missing_tool(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    app.state.mcp_registry = MCPToolRegistry()
    client = TestClient(app)
    response = client.get("/api/v1/tools/unknown")
    assert response.status_code == 404


def test_tools_invoke_endpoint_success(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    registry = MCPToolRegistry()
    registry.register_server({"server_name": "filesystem", "transport": "stdio", "endpoint": "", "enabled": True})
    registry.register_tool(
        {
            "tool_name": "read_file",
            "server_name": "filesystem",
            "description": "Read file",
            "input_schema": {"type": "object"},
            "tags": ["filesystem"],
            "enabled": True,
        }
    )
    app.state.mcp_registry = registry

    def _invoker(*, tool_name: str, arguments: dict[str, object]):
        return {"tool_name": tool_name, "arguments": dict(arguments)}

    app.state.mcp_tool_invoker = _invoker
    client = TestClient(app)
    response = client.post("/api/v1/tools/read_file/invoke", json={"arguments": {"path": "a.txt"}})
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"receipt", "result", "error"}
    assert payload["receipt"]["status"] == "succeeded"
    assert payload["result"]["tool_name"] == "read_file"


def test_tools_invoke_endpoint_blocked(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "feature_reasoning_api", True, raising=False)
    registry = MCPToolRegistry()
    registry.register_server({"server_name": "local", "transport": "stdio", "endpoint": "", "enabled": True})
    registry.register_tool(
        {
            "tool_name": "run_shell",
            "server_name": "local",
            "description": "Execute shell command",
            "input_schema": {"type": "object"},
            "tags": ["execution"],
            "enabled": True,
        }
    )
    app.state.mcp_registry = registry

    def _invoker(*, tool_name: str, arguments: dict[str, object]):
        return {"ok": True}

    app.state.mcp_tool_invoker = _invoker
    client = TestClient(app)
    response = client.post("/api/v1/tools/run_shell/invoke", json={"arguments": {"cmd": "ls"}})
    assert response.status_code == 403
