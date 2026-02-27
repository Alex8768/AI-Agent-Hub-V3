from __future__ import annotations

from pathlib import Path

from src.core.config import get_settings


def get_database_url() -> str:
    """
    SQLAlchemy async URL for Base layer.

    Defaults to local SQLite DB in settings.db_dir (cross-platform).
    """
    settings = get_settings()
    url = getattr(settings, "database_url", None)
    if url:
        return url

    # Canonical default (single source of truth)
    db_path: Path = (settings.db_dir / "ai_agent_hub.db").resolve()
    # SQLAlchemy expects forward slashes for sqlite file URLs
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"
