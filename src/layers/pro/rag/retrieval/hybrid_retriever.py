from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.providers import get_graph_store, get_memory_store
from src.core.config import get_settings


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
    results: list[dict[str, Any]] = field(default_factory=list)  # normalized vector results for reasoning.normalizer


class HybridRetriever:
    """Hybrid retrieval (Pro):

    Sources:
      - Vector retrieval (Base): engine.search()
      - Memory retrieval (Pro): semantic_query (Qdrant) or fallback query (LIKE)
      - Graph augmentation (Pro): GraphStore neighbors

    Output contract (for reasoning.normalizer):
      {
        "results": [{"chunk_id": ...}, ...],
        "graph": {"nodes": [{"id": ...}], "edges": [{"id": ...}]},
        "evidence": [{"type": "...", "id": "...", "source_refs": [...], ...}, ...]
      }
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
        memory_limit: int = 5,
    ) -> HybridRetrievalResult:
        s = get_settings()

        # 1) Vector search (Base behavior)
        vector_results = await engine.search(
            query=query,
            k=k,
            filters=filters,
            similarity_threshold=similarity_threshold,
            workspace_id=workspace_id,
        )

        # Normalize vector results into reasoning-friendly 'results' + 'evidence'
        results_norm: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []

        for r in (vector_results or []):
            chunk_id = getattr(r, "chunk_id", None) or getattr(r, "id", None)
            if not chunk_id:
                continue
            score = getattr(r, "score", None)
            meta = getattr(r, "metadata", None) or getattr(r, "meta", None) or {}
            if not isinstance(meta, dict):
                meta = {}

            results_norm.append({"chunk_id": str(chunk_id), "score": score, "meta": meta})

            src_refs = meta.get("source_refs") or meta.get("sources") or meta.get("source") or []
            if isinstance(src_refs, str):
                src_refs = [src_refs]
            if not isinstance(src_refs, list):
                src_refs = []
            evidence.append(
                {
                    "type": "chunk",
                    "id": str(chunk_id),
                    "source_refs": [str(s) for s in src_refs if s],
                    "score": float(score) if score is not None else None,
                    "confidence": meta.get("confidence"),
                    "meta": meta,
                }
            )

        # 2) Memory retrieval (Pro, feature-flagged)
        # - If feature_memory_embeddings: semantic_query via Qdrant index
        # - Else if feature_memory: fallback SQL LIKE query
        if getattr(s, "feature_memory", False):
            ms = get_memory_store()
            mem_hits: list[dict[str, Any]] = []
            try:
                if getattr(s, "feature_memory_embeddings", False):
                    mem_hits = await ms.semantic_query(
                        workspace_id=workspace_id,
                        text=query,
                        limit=int(memory_limit),
                    )
                    for h in mem_hits or []:
                        key = h.get("key")
                        if not key:
                            continue
                        score = h.get("score")
                        snippet = h.get("snippet") or ""
                        payload = h.get("payload") or {}
                        if not isinstance(payload, dict):
                            payload = {}
                        evidence.append(
                            {
                                "type": "memory",
                                "id": str(key),
                                "source_refs": [str(snippet)] if snippet else [],
                                "score": float(score) if score is not None else None,
                                "confidence": payload.get("confidence"),
                                "meta": payload,
                            }
                        )
                else:
                    mem_hits = await ms.query(
                        workspace_id=workspace_id,
                        text=query,
                        limit=int(memory_limit),
                    )
                    for h in mem_hits or []:
                        key = h.get("key")
                        if not key:
                            continue
                        value = str(h.get("value") or "")
                        meta = h.get("metadata") or {}
                        if not isinstance(meta, dict):
                            meta = {}
                        evidence.append(
                            {
                                "type": "memory",
                                "id": str(key),
                                "source_refs": [value[:240]] if value else [],
                                "score": None,
                                "confidence": meta.get("confidence"),
                                "meta": meta,
                            }
                        )
            except Exception:
                # best-effort: memory is optional and must not break retrieval
                pass

        # 3) Graph augmentation (Pro, feature-flagged in providers)
        gs = get_graph_store()
        if gs is None:
            return HybridRetrievalResult(
                vector_results=vector_results,
                graph={"nodes": [], "edges": []},
                evidence=evidence,
                results=results_norm,
            )

        seeds = await gs.search_nodes(workspace_id=workspace_id, text=query, limit=int(graph_seed_limit))
        seed_ids = [n.get("node_id") for n in (seeds or []) if isinstance(n, dict) and n.get("node_id")]

        nodes_raw: list[dict[str, Any]] = []
        edges_raw: list[dict[str, Any]] = []

        for nid in seed_ids:
            sub = await gs.neighbors(
                workspace_id=workspace_id,
                node_id=str(nid),
                depth=int(graph_depth),
                limit=int(graph_limit),
            )
            nodes_raw.extend(sub.get("nodes") or [])
            edges_raw.extend(sub.get("edges") or [])

        nodes_raw = _dedup_by(nodes_raw, "node_id")
        edges_raw = _dedup_by(edges_raw, "edge_id")

        # Normalize ids to match evidence_normalizer expectations (id)
        nodes = [{"id": n.get("node_id"), **{k: v for k, v in n.items() if k != "node_id"}} for n in nodes_raw if n.get("node_id")]
        edges = [{"id": e.get("edge_id"), **{k: v for k, v in e.items() if k != "edge_id"}} for e in edges_raw if e.get("edge_id")]

        # Evidence from graph edges (source_refs)
        for e in edges_raw:
            meta = (e.get("metadata") or {})
            src_refs = meta.get("source_refs") or []
            if isinstance(src_refs, str):
                src_refs = [src_refs]
            if not isinstance(src_refs, list):
                src_refs = []
            if src_refs:
                evidence.append(
                    {
                        "type": "edge",
                        "id": str(e.get("edge_id")),
                        "source_refs": [str(s) for s in src_refs if s],
                        "confidence": meta.get("confidence"),
                        "meta": {
                            "rel_type": e.get("rel_type"),
                            "src_id": e.get("src_id"),
                            "dst_id": e.get("dst_id"),
                        },
                    }
                )

        return HybridRetrievalResult(
            vector_results=vector_results,
            graph={"nodes": nodes, "edges": edges},
            evidence=evidence,
            results=results_norm,
        )
