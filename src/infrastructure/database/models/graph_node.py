from __future__ import annotations

import datetime as dt

from sqlalchemy import String, DateTime, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    workspace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)  # stable logical id
    node_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc))

    __table_args__ = (
        Index("ix_graph_nodes_ws_nodeid", "workspace_id", "node_id", unique=True),
    )
