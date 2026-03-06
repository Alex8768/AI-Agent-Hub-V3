from __future__ import annotations

from typing import Any, Dict, List

from fastapi import Request
from loguru import logger

from src.api.schemas import SearchRequest, SearchResult


def get_request_id(http: Request) -> str | None:
    return (
        getattr(getattr(http, "state", None), "request_id", None)
        or http.headers.get("x-request-id")
        or http.headers.get("X-Request-ID")
        or http.headers.get("X-Request-Id")
    )


def log_observability(http: Request, *, workspace_id: str, req: SearchRequest, kind: str) -> None:
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

    def _format_results(self, results: list[Any], request: SearchRequest) -> List[SearchResult]:
        response: List[SearchResult] = []
        for r in results or []:
            if not getattr(r, "document", None):
                continue

            doc = r.document
            content = getattr(doc, "content", "") or ""
            metadata = getattr(doc, "metadata", {}) or {}
            snippet = content[: int(getattr(request, "snippet_len", 200) or 200)]

            response.append(
                SearchResult(
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
        request: SearchRequest,
        *,
        workspace_id: str,
        engine: Any | None = None,
    ) -> List[SearchResult]:
        log_observability(http, workspace_id=workspace_id, req=request, kind="vector")

        from src.layers.base.rag.engines.rag_engine import RAGEngine

        engine = engine or getattr(http.app.state, "rag_engine", None) or RAGEngine()

        results = await engine.search(
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold,
            workspace_id=workspace_id,
        )
        return self._format_results(results, request)

    async def search_hybrid(
        self,
        http: Request,
        request: SearchRequest,
        *,
        workspace_id: str,
        graph_depth: int = 1,
        engine: Any | None = None,
        retriever: Any | None = None,
    ) -> Dict[str, Any]:
        log_observability(http, workspace_id=workspace_id, req=request, kind="hybrid")

        from src.layers.base.rag.engines.rag_engine import RAGEngine
        from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever

        engine = engine or getattr(http.app.state, "rag_engine", None) or RAGEngine()

        # Prefer process singleton if present, otherwise create per call (keeps Base path working)
        retriever = retriever or getattr(http.app.state, "hybrid_retriever", None) or HybridRetriever()

        out = await retriever.retrieve(
            engine=engine,
            workspace_id=workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=request.similarity_threshold,
            graph_depth=int(graph_depth or 1),
        )

        # out may be object-like or dict-like depending on retriever evolution
        vector_results = getattr(out, "vector_results", None)
        graph = getattr(out, "graph", None)
        evidence = getattr(out, "evidence", None)

        if isinstance(out, dict):
            vector_results = out.get("vector_results") or out.get("results")
            graph = out.get("graph")
            evidence = out.get("evidence")

        response = self._format_results(list(vector_results or []), request)

        return {
            "results": response,
            "graph": graph,
            "evidence": evidence,
        }
