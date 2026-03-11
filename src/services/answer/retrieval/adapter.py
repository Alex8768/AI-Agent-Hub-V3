from __future__ import annotations

from src.adapters.logging_adapter import get_logger


_LOGGER = get_logger()


class RetrieverAdapter:
    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        self._engine = engine
        self._hybrid = hybrid
        self._workspace_id = workspace_id
        self.last_stats: dict[str, object] = {}
        self.last_top_evidence: list[str] = []

    async def retrieve(self, request: object):
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=getattr(request, "query", ""),
            k=getattr(request, "k", 0),
            filters=getattr(request, "filters", None),
            similarity_threshold=0.0,
            graph_depth=getattr(request, "graph_depth", 0),
            evidence_max_total=int(getattr(request, "evidence_max_total", 50) or 50),
            evidence_max_chunks=getattr(request, "evidence_max_chunks", None),
            evidence_max_memory=getattr(request, "evidence_max_memory", None),
            evidence_max_edges=getattr(request, "evidence_max_edges", None),
            evidence_dedupe=bool(getattr(request, "evidence_dedupe", True)),
            evidence_rerank=bool(getattr(request, "evidence_rerank", True)),
        )

        graph = getattr(out, "graph", None)
        evidence = getattr(out, "evidence", None)
        results = getattr(out, "results", None)

        if isinstance(out, dict):
            graph = out.get("graph")
            evidence = out.get("evidence")
            results = out.get("results")

        graph = graph or {"nodes": [], "edges": []}
        evidence = list(evidence or [])
        results = list(results or [])

        try:
            stats = out.get("stats") if isinstance(out, dict) else getattr(out, "stats", None)
            if isinstance(stats, dict) and stats:
                self.last_stats = dict(self.last_stats or {})
                for key, value in stats.items():
                    self.last_stats.setdefault(str(key), value)
        except Exception as exc:
            _LOGGER.warning(
                "Answer service soft-failure: retriever adapter stats merge skipped",
                context={
                    "workspace_id": str(self._workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_retriever_adapter_stats_merge_soft_failure",
                },
            )

        self.last_stats = dict(self.last_stats or {})
        try:
            self.last_stats.setdefault("vector_candidates_count", int(len(results or [])))
            self.last_stats.setdefault("graph_nodes_count", int(len((graph or {}).get("nodes") or [])))
            self.last_stats.setdefault("graph_edges_count", int(len((graph or {}).get("edges") or [])))
            self.last_stats.setdefault("evidence_after_policy_count", int(len(evidence or [])))
        except Exception as exc:
            _LOGGER.warning(
                "Answer service soft-failure: retriever adapter additive stats skipped",
                context={
                    "workspace_id": str(self._workspace_id or ""),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "reason_code": "answer_service_retriever_adapter_additive_stats_soft_failure",
                },
            )

        try:
            tops: list[str] = []
            for item in (evidence or [])[:10]:
                if isinstance(item, dict):
                    chunk_id = item.get("chunk_id") or item.get("id") or item.get("doc_id")
                    if chunk_id:
                        tops.append(f"chunk:{chunk_id}")
                else:
                    s = str(item)
                    if s:
                        tops.append(f"chunk:{s}")
            self.last_top_evidence = tops
        except Exception:
            self.last_top_evidence = []
        return {"results": results, "graph": graph, "evidence": evidence}
