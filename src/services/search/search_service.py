from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Request
from loguru import logger

from src.observability.request_context import get_request_id
from src.services.search.contracts import SearchServiceRequest, SearchServiceResult


def _coerce_request(request: Any) -> SearchServiceRequest:
    if isinstance(request, SearchServiceRequest):
        return request
    if isinstance(request, dict):
        return SearchServiceRequest.model_validate(request)
    return SearchServiceRequest.model_validate(request, from_attributes=True)


def log_observability(http: Request, *, workspace_id: str, req: SearchServiceRequest, kind: str) -> None:
    try:
        rid = get_request_id(http)
        logger.info(
            "search.endpoint kind={} request_id={} workspace={} qlen={} k={}",
            kind,
            rid,
            workspace_id,
            len(req.query or ""),
            int(req.k or 0),
        )
    except Exception:
        pass


class SearchService:
    """Composition-friendly orchestration for /search and /search-hybrid endpoints."""

    def _format_results(self, results: list[Any], request: SearchServiceRequest) -> List[SearchServiceResult]:
        response: List[SearchServiceResult] = []
        for r in results or []:
            if not getattr(r, "document", None):
                continue

            doc = r.document
            content = getattr(doc, "content", "") or ""
            metadata = getattr(doc, "metadata", {}) or {}
            snippet = content[: int(getattr(request, "snippet_len", 200) or 200)]

            response.append(
                SearchServiceResult(
                    document_id=metadata.get("document_id", ""),
                    chunk_id=getattr(doc, "id", ""),
                    score=float(getattr(r, "score", 0.0) or 0.0),
                    snippet=snippet,
                    content=content if bool(getattr(request, "include_content", False)) else None,
                    source_document=metadata.get("filename"),
                    metadata=(metadata if bool(getattr(request, "include_metadata", False)) else {}),
                )
            )
        return response

    async def search(
        self,
        http: Request,
        request: SearchServiceRequest | dict[str, Any] | Any,
        *,
        workspace_id: str,
        engine: Any | None = None,
    ) -> List[SearchServiceResult]:
        req = _coerce_request(request)
        log_observability(http, workspace_id=workspace_id, req=req, kind="vector")

        from src.layers.base.rag.engines.rag_engine import RAGEngine

        engine = engine or getattr(http.app.state, "rag_engine", None) or RAGEngine()

        results = await engine.search(
            query=req.query,
            k=req.k,
            filters=req.filters,
            similarity_threshold=req.similarity_threshold,
            workspace_id=workspace_id,
        )
        return self._format_results(results, req)

    async def search_hybrid(
        self,
        http: Request,
        request: SearchServiceRequest | dict[str, Any] | Any,
        *,
        workspace_id: str,
        graph_depth: int = 1,
        engine: Any | None = None,
        retriever: Any | None = None,
    ) -> Dict[str, Any]:
        req = _coerce_request(request)
        log_observability(http, workspace_id=workspace_id, req=req, kind="hybrid")

        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever

        engine = engine or getattr(http.app.state, "rag_engine", None) or RAGEngine()

        # Prefer process singleton if present, otherwise create per call (keeps Base path working)
        retriever = retriever or getattr(http.app.state, "hybrid_retriever", None) or HybridRetriever()

        out = await retriever.retrieve(
            engine=engine,
            workspace_id=workspace_id,
            query=req.query,
            k=req.k,
            filters=req.filters,
            similarity_threshold=req.similarity_threshold,
            graph_depth=int(graph_depth or 1),
            evidence_max_total=int(req.evidence_max_total or 50),
            evidence_max_chunks=req.evidence_max_chunks,
            evidence_max_memory=req.evidence_max_memory,
            evidence_max_edges=req.evidence_max_edges,
            evidence_dedupe=bool(req.evidence_dedupe),
            evidence_rerank=bool(req.evidence_rerank),
        )

        # out may be object-like or dict-like depending on retriever evolution
        vector_results = getattr(out, "vector_results", None)
        graph = getattr(out, "graph", None)
        evidence = getattr(out, "evidence", None)
        stats = getattr(out, "stats", None)

        if isinstance(out, dict):
            vector_results = out.get("vector_results") or out.get("results")
            graph = out.get("graph")
            evidence = out.get("evidence")
            stats = out.get("stats")

        response = self._format_results(list(vector_results or []), req)

        return {
            "results": response,
            "graph": graph,
            "evidence": evidence,
            "stats": (stats if isinstance(stats, dict) else {}),
        }
