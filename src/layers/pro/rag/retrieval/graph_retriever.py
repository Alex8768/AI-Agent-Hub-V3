from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import get_settings
from src.core.providers import get_graph_store


def _dedup_by(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        item_id = item.get(key)
        if not item_id:
            continue
        sid = str(item_id)
        if sid in seen:
            continue
        seen.add(sid)
        out.append(item)
    return out


@dataclass
class GraphRetrievalResult:
    graph: dict[str, Any]
    seed_ids: list[str]
    stats: dict[str, Any]


class GraphRetriever:
    """Graph-only retriever for entity graph expansion."""

    async def retrieve(
        self,
        *,
        workspace_id: str,
        query: str,
        graph_depth: int = 1,
        graph_seed_limit: int = 5,
        graph_limit: int = 80,
    ) -> GraphRetrievalResult:
        s = get_settings()
        if not bool(getattr(s, "feature_graphrag", False)):
            return GraphRetrievalResult(
                graph={"nodes": [], "edges": []},
                seed_ids=[],
                stats={"enabled": False, "reason": "feature_graphrag_off"},
            )

        gs = get_graph_store()
        if gs is None:
            return GraphRetrievalResult(
                graph={"nodes": [], "edges": []},
                seed_ids=[],
                stats={"enabled": False, "reason": "graph_store_unavailable"},
            )

        seeds = await gs.search_nodes(workspace_id=workspace_id, text=query, limit=int(graph_seed_limit))
        seed_ids = [str(n.get("node_id")) for n in (seeds or []) if isinstance(n, dict) and n.get("node_id")]

        nodes_raw: list[dict[str, Any]] = []
        edges_raw: list[dict[str, Any]] = []
        for node_id in seed_ids:
            sub = await gs.neighbors(
                workspace_id=workspace_id,
                node_id=node_id,
                depth=int(graph_depth),
                limit=int(graph_limit),
            )
            nodes_raw.extend(sub.get("nodes") or [])
            edges_raw.extend(sub.get("edges") or [])

        nodes_raw = _dedup_by(nodes_raw, "node_id")
        edges_raw = _dedup_by(edges_raw, "edge_id")

        nodes = [
            {"id": n.get("node_id"), **{k: v for k, v in n.items() if k != "node_id"}}
            for n in nodes_raw
            if n.get("node_id")
        ]
        edges = [
            {"id": e.get("edge_id"), **{k: v for k, v in e.items() if k != "edge_id"}}
            for e in edges_raw
            if e.get("edge_id")
        ]

        return GraphRetrievalResult(
            graph={"nodes": nodes, "edges": edges},
            seed_ids=seed_ids,
            stats={
                "enabled": True,
                "seed_count": len(seed_ids),
                "node_count": len(nodes),
                "edge_count": len(edges),
                "graph_depth": int(graph_depth),
                "graph_limit": int(graph_limit),
            },
        )
