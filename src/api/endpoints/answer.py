from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.config import get_settings
from src.core.providers import get_reasoning_engine
from src.api.dependencies import get_workspace
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse


router = APIRouter(prefix="/api/v1", tags=["reasoning"])


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

    # Observability (MVP): correlate request + workspace (best-effort, non-fatal)
    try:
        from loguru import logger

        rid = (
            getattr(getattr(http, "state", None), "request_id", None)
            or http.headers.get("x-request-id")
            or http.headers.get("X-Request-ID")
            or http.headers.get("X-Request-Id")
        )
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

    # Composition root (MVP):
    # - retriever/llm are injected from the outer layer later.
    # For now we fail-fast until proper DI wiring is added.
    from src.layers.base.rag.engines.rag_engine import RAGEngine
    from src.layers.pro.rag.retrieval.hybrid_retriever import HybridRetriever

    engine = getattr(http.app.state, "rag_engine", None)
    if engine is None:
        engine = RAGEngine()
        http.app.state.rag_engine = engine
    hybrid = getattr(http.app.state, "hybrid_retriever", None)
    if hybrid is None:
        hybrid = HybridRetriever()
        http.app.state.hybrid_retriever = hybrid

    # Lazy LLM provider acquisition (do not resolve dependencies before feature-gate)
    llm = None
    try:
        from src.api.dependencies_impl import get_llm_provider
        llm = await get_llm_provider()
    except Exception:
        llm = None

    class _RetrieverAdapter:
        async def retrieve(self, request: AnswerRequest):
            out = await hybrid.retrieve(
                engine=engine,
                workspace_id=workspace_id,
                query=request.query,
                k=request.k,
                filters=request.filters,
                similarity_threshold=0.0,
                graph_depth=request.graph_depth,
            )
            # ReasoningEngine expects dict-like shape with evidence/graph (vector results optional here)
            return {"results": [], "graph": out.graph, "evidence": out.evidence}

    reasoning = get_reasoning_engine(retriever=_RetrieverAdapter(), llm=llm)
    if reasoning is None:
        raise HTTPException(status_code=404, detail="Not Found")

    # Observability (MVP): correlate request + workspace (best-effort, non-fatal)
    try:
        from loguru import logger

        rid = (
            getattr(getattr(http, "state", None), "request_id", None)
            or http.headers.get("x-request-id")
            or http.headers.get("X-Request-ID")
            or http.headers.get("X-Request-Id")
        )
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

    return await reasoning.synthesize(req)
