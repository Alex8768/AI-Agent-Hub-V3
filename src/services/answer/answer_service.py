from __future__ import annotations

from time import perf_counter
from typing import Any

from fastapi import Request

from src.layers.pro.reasoning.contracts import AnswerRequest


def get_request_id(http: Request) -> str | None:
    return (
        getattr(getattr(http, "state", None), "request_id", None)
        or http.headers.get("x-request-id")
        or http.headers.get("X-Request-ID")
        or http.headers.get("X-Request-Id")
    )


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
