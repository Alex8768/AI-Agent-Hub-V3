from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.providers import get_graph_store


def _dedup_by(items: List[dict], key: str) -> List[dict]:
    seen = set()
    out = []
    for it in items:
        k = it.get(key)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


@dataclass
class HybridRetrievalResult:
    vector_results: list[Any]
    graph: dict[str, Any]
    evidence: list[dict[str, Any]]


class HybridRetriever:
    """
    Hybrid retrieval MVP:
    - Vector retrieval via existing engine.search()
    - Optional GraphRAG augmentation (if feature_graphrag enabled)
    """

    async def retrieve(
        self,
        *,
        engine: Any,
        workspace_id: str,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None,
        graph_depth: int = 1,
        graph_seed_limit: int = 5,
        graph_limit: int = 80,
    ) -> HybridRetrievalResult:
        # 1) Vector search (Base behavior)
        vector_results = await engine.search(
            query=query,
            k=k,
            filters=filters,
            similarity_threshold=similarity_threshold,
            workspace_id=workspace_id,
        )

        # 2) Graph augmentation (Pro, feature-flagged in providers)
        gs = get_graph_store()
        if gs is None:
            return HybridRetrievalResult(vector_results=vector_results, graph={"nodes": [], "edges": []}, evidence=[])

        # Seed nodes by query text
        seeds = await gs.search_nodes(workspace_id=workspace_id, text=query, limit=int(graph_seed_limit))
        seed_ids = [n["node_id"] for n in seeds if n.get("node_id")]

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        # Expand neighbors
        for nid in seed_ids:
            sub = await gs.neighbors(workspace_id=workspace_id, node_id=nid, depth=int(graph_depth), limit=int(graph_limit))
            nodes.extend(sub.get("nodes") or [])
            edges.extend(sub.get("edges") or [])

        nodes = _dedup_by(nodes, "node_id")
        edges = _dedup_by(edges, "edge_id")

        # Evidence extraction for UI (source_refs)
        evidence: list[dict[str, Any]] = []
        for e in edges:
            meta = (e.get("metadata") or {})
            src_refs = meta.get("source_refs") or []
            if src_refs:
                evidence.append(
                    {
                        "type": "edge",
                        "edge_id": e.get("edge_id"),
                        "rel_type": e.get("rel_type"),
                        "src_id": e.get("src_id"),
                        "dst_id": e.get("dst_id"),
                        "source_refs": src_refs,
                        "confidence": meta.get("confidence"),
                    }
                )

        return HybridRetrievalResult(vector_results=vector_results, graph={"nodes": nodes, "edges": edges}, evidence=evidence)
