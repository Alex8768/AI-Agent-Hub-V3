from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.config import get_settings
from src.core.providers import get_reasoning_engine
from src.api.dependencies import get_workspace
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse


router = APIRouter(prefix="/api/v1", tags=["reasoning"])


def _get_request_id(http: Request) -> str | None:
    return (
        getattr(getattr(http, "state", None), "request_id", None)
        or http.headers.get("x-request-id")
        or http.headers.get("X-Request-ID")
        or http.headers.get("X-Request-Id")
    )


def _log_observability(http: Request, *, workspace_id: str, req: AnswerRequest) -> None:
    # best-effort, non-fatal
    try:
        from loguru import logger

        rid = _get_request_id(http)
        logger.info(
            "answer.endpoint request_id={} workspace={} qlen={} k={} depth={}",
            rid,
            workspace_id,
            len(req.query or ""),
            int(req.k or 0),
            int(req.graph_depth or 0),
        )
    except Exception:
        pass


class _RetrieverAdapter:
    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        self._engine = engine
        self._hybrid = hybrid
        self._workspace_id = workspace_id

    async def retrieve(self, request: AnswerRequest):
        # HybridRetriever API: retrieve(engine=..., workspace_id=..., ...)
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=0.0,
            graph_depth=request.graph_depth,
        )
        # ReasoningEngine expects dict-like shape with evidence/graph
        return {"results": [], "graph": getattr(out, "graph", None), "evidence": getattr(out, "evidence", [])}


@router.post("/answer", response_model=AnswerResponse)
async def answer(
    http: Request,
    req: AnswerRequest,
    workspace_id: str = Depends(get_workspace),
) -> AnswerResponse:
    """Graph-aware answer synthesis (Pro).

    Feature-gated:
      - feature_reasoning
      - feature_graphrag
    """
    s = get_settings()
    if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
        # Hide Pro API surface when disabled
        raise HTTPException(status_code=404, detail="Not Found")

    _log_observability(http, workspace_id=workspace_id, req=req)

    # Composition root rule:
    # - heavyweight deps must be wired in lifespan (or outer layer), not inside endpoint.
    engine = getattr(http.app.state, "rag_engine", None)
    hybrid = getattr(http.app.state, "hybrid_retriever", None)
    if engine is None or hybrid is None:
        raise HTTPException(status_code=503, detail="Reasoning stack not initialized")

    # Lazy LLM provider acquisition (do not resolve dependencies before feature-gate)
    llm = None
    try:
        from src.api.dependencies_impl import get_llm_provider

        llm = await get_llm_provider()
    except Exception:
        llm = None

    retriever = _RetrieverAdapter(engine=engine, hybrid=hybrid, workspace_id=workspace_id)

    reasoning = get_reasoning_engine(retriever=retriever, llm=llm)
    if reasoning is None:
        raise HTTPException(status_code=404, detail="Not Found")

    t0 = perf_counter()
    resp = await reasoning.synthesize(req)
    total_ms = (perf_counter() - t0) * 1000.0

    # Enrich response with API-level correlation/timings (contract v1)
    try:
        resp.request_id = _get_request_id(http) or ""
    except Exception:
        resp.request_id = ""
    try:
        resp.workspace_id = workspace_id or ""
    except Exception:
        resp.workspace_id = ""

    try:
        resp.timings = dict(resp.timings or {})
        resp.timings.setdefault("total_ms", float(total_ms))
    except Exception:
        pass

    try:
        if llm is None:
            resp.warnings = list(resp.warnings or [])
            if "llm_missing" not in resp.warnings:
                resp.warnings.append("llm_missing")
    except Exception:
        pass

    return resp
