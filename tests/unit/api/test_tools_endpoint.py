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
