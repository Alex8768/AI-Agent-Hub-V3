from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.providers import get_memory_store
from src.core.config import get_settings
from src.layers.pro.rag.retrieval.graph_retriever import GraphRetriever


@dataclass
class HybridRetrievalResult:
    vector_results: list[Any]
    graph: dict[str, Any]
    evidence: list[dict[str, Any]]
    results: list[dict[str, Any]] = field(default_factory=list)  # normalized vector results for reasoning.normalizer
    stats: dict[str, Any] = field(default_factory=dict)  # retrieval diagnostics (memory/vector/graph)


class HybridRetriever:
    """Hybrid retrieval (Pro):

    Sources:
      - Vector retrieval (Base): engine.search() -> SearchResult(document=VectorDocument, score, distance)
      - Memory retrieval (Pro): semantic_query (Qdrant) or fallback query (LIKE)
      - Graph augmentation (Pro): GraphStore neighbors

    Output contract (for reasoning.normalizer):
      {
        "results": [{"chunk_id": ...}, ...],
        "graph": {"nodes": [{"id": ...}], "edges": [{"id": ...}]},
        "evidence": [{"type": "...", "id": "...", "source_refs": [...], ...}, ...]
      }
    """

    def __init__(self, *, graph_retriever: GraphRetriever | None = None) -> None:
        self._graph_retriever = graph_retriever or GraphRetriever()

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
            # RAGEngine.search() returns src.core.contracts.contracts.SearchResult:
            # {document: VectorDocument, score: float, distance: float}
            doc = getattr(r, "document", None)
            if doc is None:
                continue

            meta = getattr(doc, "metadata", None) or {}
            if not isinstance(meta, dict):
                meta = {}

            # Prefer explicit chunk_id from metadata; fallback to VectorDocument.id
            chunk_id = meta.get("chunk_id") or getattr(doc, "id", None)
            if not chunk_id:
                continue

            score = getattr(r, "score", None)

            # results_norm drives used_chunks in reasoning.normalizer
            results_norm.append({"chunk_id": str(chunk_id), "score": score, "meta": meta})

            # Evidence item for provenance (chunk)
            content_preview = getattr(doc, "content", None) or ""
            src_refs = meta.get("source_refs") or meta.get("sources") or meta.get("source")
            if not src_refs:
                src_refs = [content_preview] if content_preview else []
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
        mem_mode = "off"
        mem_candidates = 0
        mem_added = 0

        if getattr(s, "feature_memory", False):
            ms = get_memory_store()
            mem_hits: list[dict[str, Any]] = []
            try:
                if getattr(s, "feature_memory_embeddings", False):
                    mem_mode = "semantic"
                    mem_hits = await ms.semantic_query(
                        workspace_id=workspace_id,
                        text=query,
                        limit=int(memory_limit),
                    )
                    mem_candidates = int(len(mem_hits or []))
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
                        mem_added += 1
                else:
                    mem_mode = "like"
                    mem_hits = await ms.query(
                        workspace_id=workspace_id,
                        text=query,
                        limit=int(memory_limit),
                    )
                    mem_candidates = int(len(mem_hits or []))
                    for h in mem_hits or []:
                        key = h.get("key")
                        if not key:
                            continue
                        value = str(h.get("value") or "")
                        meta2 = h.get("metadata") or {}
                        if not isinstance(meta2, dict):
                            meta2 = {}
                        evidence.append(
                            {
                                "type": "memory",
                                "id": str(key),
                                "source_refs": [value[:240]] if value else [],
                                "score": None,
                                "confidence": meta2.get("confidence"),
                                "meta": meta2,
                            }
                        )
                        mem_added += 1
            except Exception:
                # best-effort: memory must not break retrieval
                pass

        stats: dict[str, Any] = {
            "memory_mode": mem_mode,
            "memory_candidates_count": mem_candidates,
            "memory_added_evidence_count": mem_added,
        }

        # 3) Graph augmentation (Pro, delegated to GraphRetriever)
        graph_out = await self._graph_retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            graph_depth=graph_depth,
            graph_seed_limit=graph_seed_limit,
            graph_limit=graph_limit,
        )
        graph = graph_out.graph or {"nodes": [], "edges": []}
        graph_edges = list(graph.get("edges") or [])
        stats.update(
            {
                "graph_enabled": bool(graph_out.stats.get("enabled", False)),
                "graph_seed_count": int(graph_out.stats.get("seed_count", 0)),
                "graph_node_count": int(graph_out.stats.get("node_count", len(graph.get("nodes") or []))),
                "graph_edge_count": int(graph_out.stats.get("edge_count", len(graph_edges))),
            }
        )

        # Evidence from graph edges (source_refs)
        for e in graph_edges:
            meta3 = (e.get("metadata") or {})
            src_refs3 = meta3.get("source_refs") or []
            if isinstance(src_refs3, str):
                src_refs3 = [src_refs3]
            if not isinstance(src_refs3, list):
                src_refs3 = []
            if src_refs3:
                evidence.append(
                    {
                        "type": "edge",
                        "id": str(e.get("id") or e.get("edge_id")),
                        "source_refs": [str(s) for s in src_refs3 if s],
                        "confidence": meta3.get("confidence"),
                        "meta": {
                            "rel_type": e.get("rel_type"),
                            "src_id": e.get("src_id"),
                            "dst_id": e.get("dst_id"),
                        },
                    }
                )

        return HybridRetrievalResult(
            vector_results=vector_results,
            graph=graph,
            evidence=evidence,
            results=results_norm,
            stats=stats,
        )
