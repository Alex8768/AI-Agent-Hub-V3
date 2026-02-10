from __future__ import annotations

from src.core.config import get_settings


def get_database_url() -> str:
    """
    SQLAlchemy async URL for Base layer.

    Defaults to local SQLite DB in ./data/ai_agent_hub.db
    """
    settings = get_settings()
    url = getattr(settings, "database_url", None)
    if url:
        return url
    return "sqlite+aiosqlite:///./data/ai_agent_hub.db"
