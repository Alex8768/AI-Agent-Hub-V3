from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.graph_node import GraphNode
from src.infrastructure.database.models.graph_edge import GraphEdge


@dataclass
class GraphStore:
    """DB-backed graph store (per-session)."""
    db: AsyncSession

    async def upsert_node(
        self,
        *,
        workspace_id: str,
        node_id: str,
        node_type: str,
        name: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        meta = dict(metadata or {})
        q = select(GraphNode).where(GraphNode.workspace_id == workspace_id, GraphNode.node_id == node_id)
        res = await self.db.execute(q)
        row = res.scalar_one_or_none()
        if row is None:
            self.db.add(GraphNode(workspace_id=workspace_id, node_id=node_id, node_type=node_type, name=name, meta=meta))
        else:
            row.node_type = node_type
            row.name = name
            row.meta = meta
        await self.db.commit()

    async def upsert_edge(
        self,
        *,
        workspace_id: str,
        edge_id: str,
        src_id: str,
        dst_id: str,
        rel_type: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        meta = dict(metadata or {})
        q = select(GraphEdge).where(GraphEdge.workspace_id == workspace_id, GraphEdge.edge_id == edge_id)
        res = await self.db.execute(q)
        row = res.scalar_one_or_none()
        if row is None:
            self.db.add(
                GraphEdge(
                    workspace_id=workspace_id,
                    edge_id=edge_id,
                    src_id=src_id,
                    dst_id=dst_id,
                    rel_type=rel_type,
                    meta=meta,
                )
            )
        else:
            row.src_id = src_id
            row.dst_id = dst_id
            row.rel_type = rel_type
            row.meta = meta
        await self.db.commit()

    async def search_nodes(self, *, workspace_id: str, text: str, limit: int = 20) -> list[dict[str, Any]]:
        pattern = f"%{text}%"
        q = (
            select(GraphNode)
            .where(GraphNode.workspace_id == workspace_id)
            .where(or_(GraphNode.name.like(pattern), GraphNode.node_id.like(pattern)))
            .order_by(GraphNode.id.desc())
            .limit(int(limit))
        )
        res = await self.db.execute(q)
        rows = res.scalars().all()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append({"node_id": r.node_id, "node_type": r.node_type, "name": r.name, "metadata": dict(r.meta or {})})
        return out

    async def neighbors(
        self,
        *,
        workspace_id: str,
        node_id: str,
        depth: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Expand neighbors up to depth (BFS).
        Returns: {"nodes": [...], "edges": [...]}
        """
        depth = max(1, int(depth))
        limit = max(1, int(limit))

        visited = set([node_id])
        frontier = [node_id]

        edges_out: list[dict[str, Any]] = []
        nodes_out: dict[str, dict[str, Any]] = {}

        # helper: load node details
        async def _load_nodes(ids: list[str]) -> None:
            if not ids:
                return
            q = select(GraphNode).where(GraphNode.workspace_id == workspace_id, GraphNode.node_id.in_(ids))
            res = await self.db.execute(q)
            for r in res.scalars().all():
                nodes_out[r.node_id] = {"node_id": r.node_id, "node_type": r.node_type, "name": r.name, "metadata": dict(r.meta or {})}

        await _load_nodes([node_id])

        for _ in range(depth):
            if not frontier or len(edges_out) >= limit:
                break

            q = (
                select(GraphEdge)
                .where(GraphEdge.workspace_id == workspace_id)
                .where(or_(GraphEdge.src_id.in_(frontier), GraphEdge.dst_id.in_(frontier)))
                .limit(int(limit - len(edges_out)))
            )
            res = await self.db.execute(q)
            batch = res.scalars().all()

            next_frontier: list[str] = []
            for e in batch:
                edges_out.append(
                    {
                        "edge_id": e.edge_id,
                        "src_id": e.src_id,
                        "dst_id": e.dst_id,
                        "rel_type": e.rel_type,
                        "metadata": dict(e.meta or {}),
                    }
                )
                for nid in (e.src_id, e.dst_id):
                    if nid not in visited:
                        visited.add(nid)
                        next_frontier.append(nid)

            frontier = next_frontier
            await _load_nodes(frontier)

        return {"nodes": list(nodes_out.values()), "edges": edges_out}
