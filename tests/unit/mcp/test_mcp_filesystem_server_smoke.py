from __future__ import annotations

import importlib


def test_mcp_filesystem_server_import_smoke():
    m = importlib.import_module("mcp_servers.filesystem.server")
    assert hasattr(m, "main")
    assert callable(m.main)
