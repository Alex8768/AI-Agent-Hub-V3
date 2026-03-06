from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import Request

from src.layers.pro.reasoning.contracts import AnswerRequest
from src.observability.request_context import get_request_id


def log_observability(http: Request, *, workspace_id: str, req: AnswerRequest) -> None:
    try:
        from loguru import logger

        rid = get_request_id(http)
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


class RetrieverAdapter:
    def __init__(self, *, engine: object, hybrid: object, workspace_id: str):
        self._engine = engine
        self._hybrid = hybrid
        self._workspace_id = workspace_id
        self.last_stats: dict[str, object] = {}
        self.last_top_evidence: list[str] = []

    async def retrieve(self, request: AnswerRequest):
        out = await self._hybrid.retrieve(
            engine=self._engine,
            workspace_id=self._workspace_id,
            query=request.query,
            k=request.k,
            filters=request.filters,
            similarity_threshold=0.0,
            graph_depth=request.graph_depth,
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

        # merge retriever stats (best-effort)
        try:
            stats = out.get("stats") if isinstance(out, dict) else getattr(out, "stats", None)
            if isinstance(stats, dict) and stats:
                self.last_stats = dict(self.last_stats or {})
                for k, v in stats.items():
                    self.last_stats.setdefault(str(k), v)
        except Exception:
            pass

        # Hybrid retriever owns evidence policy in A1.5. Keep adapter diagnostics additive only.
        self.last_stats = dict(self.last_stats or {})
        try:
            self.last_stats.setdefault("vector_candidates_count", int(len(results or [])))
            self.last_stats.setdefault("graph_nodes_count", int(len((graph or {}).get("nodes") or [])))
            self.last_stats.setdefault("graph_edges_count", int(len((graph or {}).get("edges") or [])))
            self.last_stats.setdefault("evidence_after_policy_count", int(len(evidence or [])))
        except Exception:
            pass


        # Build debug "top_evidence" list (best-effort). Test expects at least one "chunk:*" when evidence exists.
        try:
            tops: list[str] = []
            for item in (evidence or [])[:10]:
                if isinstance(item, dict):
                    cid = item.get("chunk_id") or item.get("id") or item.get("doc_id")
                    if cid:
                        tops.append(f"chunk:{cid}")
                else:
                    # If evidence is already a string/id-like, keep it as chunk reference
                    s = str(item)
                    if s:
                        tops.append(f"chunk:{s}")
            self.last_top_evidence = tops
        except Exception:
            self.last_top_evidence = []
        return {"results": results, "graph": graph, "evidence": evidence}


class LLMGenerateAdapter:
    """Adapt Base LLM provider (complete/messages) to ReasoningEngine contract (generate(prompt)->str)."""

    def __init__(self, provider: object, *, provider_name: str = "", model: str = ""):
        self._p = provider
        self.provider_name = provider_name
        self.model = model

    async def generate(self, prompt: str) -> str:
        from src.core.types import Message, MessageRole

        messages = [Message(role=MessageRole.USER, content=str(prompt or ""))]
        cfg: dict[str, Any] = {}
        if self.model:
            cfg["model"] = self.model

        if hasattr(self._p, "complete"):
            c = await self._p.complete(messages=messages, config=(cfg or None))
            text = getattr(c, "content", None)
            return str(text if text is not None else c)

        raise RuntimeError("LLM provider does not implement complete()")


class AnswerService:
    """Composition-friendly orchestration for /answer endpoint.

    Keeps FastAPI endpoint thin and concentrates gating/wiring/diagnostics here.
    """

    async def handle(
        self,
        http: Request,
        req,
        *,
        workspace_id: str,
        engine: object | None = None,
        retriever: object | None = None,
    ):
        from src.core.config import get_settings
        from src.core.providers import get_reasoning_engine

        s = get_settings()
        if not getattr(s, "feature_reasoning", False) or not getattr(s, "feature_graphrag", False):
            # Endpoint uses 404 for feature-gated routes
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        log_observability(http, workspace_id=workspace_id, req=req)

        engine = engine or getattr(http.app.state, "rag_engine", None)
        hybrid = retriever or getattr(http.app.state, "hybrid_retriever", None)
        if engine is None or hybrid is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Reasoning stack not initialized")

        llm_enabled = bool(getattr(s, "feature_reasoning_llm_enabled", False))

        llm = None
        llm_provider_name = ""
        llm_model = ""
        llm_error = ""

        if llm_enabled:
            try:
                from src.api.dependencies_impl import get_llm_provider

                prov = await get_llm_provider()
                # Determine provider/model for diagnostics in a provider-aware way
                try:
                    llm_provider_name = str(getattr(s, "llm_provider").value)
                except Exception:
                    llm_provider_name = str(getattr(s, "llm_provider", "") or "")
                if llm_provider_name == "openai":
                    llm_model = str(getattr(s, "openai_model", "") or "")
                elif llm_provider_name == "ollama":
                    llm_model = str(getattr(s, "ollama_model", "") or "")
                else:
                    llm_model = str(getattr(prov, "model", "") or "")
                llm = LLMGenerateAdapter(prov, provider_name=llm_provider_name, model=llm_model)
            except Exception as e:
                llm = None
                llm_error = str(e)

        retriever = RetrieverAdapter(engine=engine, hybrid=hybrid, workspace_id=workspace_id)
        reasoning = get_reasoning_engine(retriever=retriever, llm=llm)
        if reasoning is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        t0 = perf_counter()
        resp = await reasoning.synthesize(req)
        total_ms = (perf_counter() - t0) * 1000.0

        # correlation/timing
        try:
            resp.request_id = get_request_id(http) or ""
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
            diag.setdefault("evidence_type_counts", {})
                        # top_evidence: prefer retriever snapshot; fallback to response used_chunks
            try:
                tops = list(getattr(retriever, "last_top_evidence", []) or [])
            except Exception:
                tops = []
            if not tops:
                try:
                    tops = [f"chunk:{x}" for x in (getattr(resp, "used_chunks", []) or [])[:10]]
                except Exception:
                    tops = []
            diag.setdefault("top_evidence", tops)            # trace_id must be present in diagnostics (debug snapshot expects it)
            rid = str(get_request_id(http) or "")
            try:
                from src.observability.trace import make_trace_id

                diag.setdefault(
                    "trace_id",
                    make_trace_id(
                        workspace_id=str(workspace_id or ""),
                        request_id=rid,
                    ),
                )
            except Exception:
                # Fallback: stable correlation id even without tracing deps
                diag.setdefault("trace_id", rid or "")

            # LLM diagnostics
            diag.setdefault("llm_enabled", bool(llm_enabled))
            diag.setdefault("llm_provider", llm_provider_name)
            diag.setdefault("llm_model", llm_model)
            diag.setdefault("llm_error", llm_error)

            # Retriever stats (best-effort)
            try:
                diag.setdefault("retriever_stats", dict(getattr(retriever, "last_stats", {}) or {}))
            except Exception:
                pass

            resp.diagnostics = diag
        except Exception:
            pass

        return resp
