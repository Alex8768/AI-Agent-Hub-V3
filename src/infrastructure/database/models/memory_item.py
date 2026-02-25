from __future__ import annotations

import datetime as dt

from sqlalchemy import String, Text, DateTime, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    workspace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(256), nullable=False, index=True)

    # Plain text value (MVP). Later we can add embeddings / references.
    value: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc))

    __table_args__ = (
        Index("ix_memory_workspace_key", "workspace_id", "key"),
    )
