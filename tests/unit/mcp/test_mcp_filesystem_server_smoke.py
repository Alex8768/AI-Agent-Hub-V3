from __future__ import annotations

import importlib
import importlib.util

import pytest


def test_mcp_filesystem_server_import_smoke():
    # MCP is an optional extra. Base CI profiles may not install it.
    if importlib.util.find_spec("mcp") is None:
        pytest.skip("Optional dependency 'mcp' is not installed")

    m = importlib.import_module("mcp_servers.filesystem.server")
    assert hasattr(m, "main")
    assert callable(m.main)
