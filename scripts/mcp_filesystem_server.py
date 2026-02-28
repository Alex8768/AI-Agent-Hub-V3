"""Run MCP filesystem server (stdio) with predictable environment.

Usage:
  python scripts/mcp_filesystem_server.py

This entrypoint avoids ambiguous module execution paths and ensures
the project root is on sys.path when launched as a script.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_project_root_on_syspath() -> None:
    # scripts/ -> project root
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> None:
    _ensure_project_root_on_syspath()
    # Import after sys.path fix
    from mcp_servers.filesystem.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
