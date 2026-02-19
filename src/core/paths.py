from __future__ import annotations

import os
from pathlib import Path


def get_default_data_dir(app_name: str = "ai-agent-hub") -> Path:
    """
    Cross-platform application data directory.

    Priority:
      1) AI_AGENT_HUB_DATA_DIR env var
      2) Windows: LOCALAPPDATA (or APPDATA)
      3) Unix/macOS: ~/.<app_name>
    """
    override = os.getenv("AI_AGENT_HUB_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        return (Path(base) / app_name).expanduser().resolve()

    return (Path.home() / f".{app_name}").expanduser().resolve()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
