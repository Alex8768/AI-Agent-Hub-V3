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
        self.last_stats: dict[str, object] = {}

    async def retrieve(self, request: AnswerRequest):
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=0.0,
            graph_depth=request.graph_depth,
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

        # merge retriever stats (best-effort)
        try:
            stats = out.get("stats") if isinstance(out, dict) else getattr(out, "stats", None)
            if isinstance(stats, dict) and stats:
                self.last_stats = dict(self.last_stats or {})
                for k, v in stats.items():
                    self.last_stats.setdefault(str(k), v)
        except Exception:
            pass

        # apply policy (best-effort)
        try:
            from src.layers.pro.rag.retrieval.policy import RetrievalPolicy, apply_policy

            policy = RetrievalPolicy(
                similarity_threshold=0.0,
                max_evidence=int(getattr(request, "k", 8) or 8) * 5,
                dedupe=True,
            )
            evidence_filtered, stats = apply_policy(evidence, policy=policy)
            self.last_stats = dict(stats or {})
            try:
                self.last_stats.setdefault("vector_candidates_count", int(len(results or [])))
                self.last_stats.setdefault("graph_nodes_count", int(len((graph or {}).get("nodes") or [])))
                self.last_stats.setdefault("graph_edges_count", int(len((graph or {}).get("edges") or [])))
            except Exception:
                pass
            evidence = evidence_filtered
        except Exception:
            self.last_stats = {}

        return {"results": results, "graph": graph, "evidence": evidence}


class _LLMGenerateAdapter:
    """Adapt Base LLM provider (complete/messages) to ReasoningEngine contract (generate(prompt)->str)."""

    def __init__(self, provider: object, *, provider_name: str = "", model: str = ""):
        self._p = provider
        self.provider_name = provider_name
        self.model = model

    async def generate(self, prompt: str) -> str:
        from src.core.types import Message, MessageRole

        messages = [Message(role=MessageRole.USER, content=str(prompt or ""))]
        cfg = {}
        if self.model:
            cfg["model"] = self.model

        if hasattr(self._p, "complete"):
            c = await self._p.complete(messages=messages, config=(cfg or None))
            text = getattr(c, "content", None)
            return str(text if text is not None else c)

        raise RuntimeError("LLM provider does not implement complete()")


@router.post("/answer", response_model=AnswerResponse)
async def answer(
    http: Request,
    req: AnswerRequest,
    workspace_id: str = Depends(get_workspace),
) -> AnswerResponse:
    s = get_settings()
    if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
        raise HTTPException(status_code=404, detail="Not Found")

    _log_observability(http, workspace_id=workspace_id, req=req)

    engine = getattr(http.app.state, "rag_engine", None)
    hybrid = getattr(http.app.state, "hybrid_retriever", None)
    if engine is None or hybrid is None:
        raise HTTPException(status_code=503, detail="Reasoning stack not initialized")

    # LLM resolution is gated to prevent accidental cloud calls
    llm_enabled = bool(getattr(s, "feature_reasoning_llm_enabled", False))

    llm = None
    llm_provider_name = ""
    llm_model = ""
    llm_error = ""

    if llm_enabled:
        try:
            from src.api.dependencies_impl import get_llm_provider

            p = await get_llm_provider()
            llm_provider_name = str(getattr(p, "provider", "") or getattr(s, "llm_provider", "") or "")
            llm_model = str(getattr(p, "model", "") or getattr(s, "ollama_model", "") or getattr(s, "openai_model", "") or "")
            llm = _LLMGenerateAdapter(p, provider_name=llm_provider_name, model=llm_model)
        except Exception as e:
            llm = None
            llm_error = str(e)

    retriever = _RetrieverAdapter(engine=engine, hybrid=hybrid, workspace_id=workspace_id)
    reasoning = get_reasoning_engine(retriever=retriever, llm=llm)
    if reasoning is None:
        raise HTTPException(status_code=404, detail="Not Found")

    t0 = perf_counter()
    resp = await reasoning.synthesize(req)
    total_ms = (perf_counter() - t0) * 1000.0

    # correlation/timing
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

    # base diagnostics + trace
    try:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        diag.setdefault("retrieved_provenance_count", int(len(getattr(resp, "provenance", []) or [])))
        diag.setdefault("used_chunks_count", int(len(getattr(resp, "used_chunks", []) or [])))
        diag.setdefault("used_nodes_count", int(len(getattr(resp, "used_nodes", []) or [])))
        diag.setdefault("used_edges_count", int(len(getattr(resp, "used_edges", []) or [])))
        diag.setdefault("has_llm", bool(llm is not None))
        diag.setdefault("query_len", int(len(req.query or "")))
        diag.setdefault("k", int(req.k or 0))
        diag.setdefault("graph_depth", int(req.graph_depth or 0))

        try:
            from src.observability.trace import make_trace_id

            diag.setdefault(
                "trace_id",
                make_trace_id(
                    workspace_id=str(workspace_id or ""),
                    query=str(req.query or ""),
                    k=int(req.k or 0),
                    graph_depth=int(req.graph_depth or 0),
                ),
            )
        except Exception:
            pass

        resp.diagnostics = diag
    except Exception:
        pass

    # retrieval stats
    try:
        stats = getattr(retriever, "last_stats", None) or {}
        if stats:
            diag = dict(getattr(resp, "diagnostics", None) or {})
            for k, v in dict(stats).items():
                diag.setdefault(f"retrieval_{k}", v)
            resp.diagnostics = diag
    except Exception:
        pass

    # debug snapshot
    try:
        if getattr(s, "debug", False):
            diag = dict(getattr(resp, "diagnostics", None) or {})
            counts: dict[str, int] = {}
            for pitem in (getattr(resp, "provenance", None) or []):
                t = str(getattr(pitem, "type", "") or "") or "unknown"
                counts[t] = int(counts.get(t, 0)) + 1
            diag.setdefault("evidence_type_counts", counts)

            top: list[str] = []
            for pitem in (getattr(resp, "provenance", None) or [])[:20]:
                t = str(getattr(pitem, "type", "") or "")
                i = str(getattr(pitem, "id", "") or "")
                if t and i:
                    top.append(f"{t}:{i}")
            diag.setdefault("top_evidence", top)
            resp.diagnostics = diag
    except Exception:
        pass

    # llm mode diagnostics
    try:
        diag = dict(getattr(resp, "diagnostics", None) or {})
        if llm is not None:
            diag.setdefault("llm_mode", "real")
            if llm_provider_name:
                diag.setdefault("llm_provider", llm_provider_name)
            if llm_model:
                diag.setdefault("llm_model", llm_model)
        elif bool(getattr(s, "feature_reasoning_llm_dry_run", False)):
            diag.setdefault("llm_mode", "dry_run")
        else:
            diag.setdefault("llm_mode", "disabled")

        if llm_error:
            diag.setdefault("llm_error", llm_error)

        fr = getattr(resp, "_fallback_reason", None)
        if fr:
            diag.setdefault("fallback_reason", str(fr))

        resp.diagnostics = diag
    except Exception:
        pass

    # warnings
    try:
        if llm is None and llm_enabled:
            resp.warnings = list(resp.warnings or [])
            if "llm_missing" not in resp.warnings:
                resp.warnings.append("llm_missing")
    except Exception:
        pass

    return resp
