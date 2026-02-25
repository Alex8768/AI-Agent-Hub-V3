from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro).

    Orchestration layer above retrieval (HybridRetriever-compatible).
    Architecture rules:
      - dependency injection for retriever/llm (llm later)
      - no side effects in __init__
      - schema-first contracts in reasoning.contracts
    """

    retriever: object
    llm: object | None = None
    llm_timeout_s: float = 15.0

    async def synthesize(self, request):
        """Synthesize an answer from retrieval evidence.

        MVP: orchestration only (no LLM yet).
        - Calls injected retriever
        - Pass-through provenance (best-effort) if retriever provides it
        - Returns deterministic stub answer
        """
        # Observability (MVP): latency + key counters
        from time import perf_counter
        t0 = perf_counter()
        result = await self.retriever.retrieve(request)


        from src.layers.pro.reasoning.contracts import AnswerResponse
        from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
        from src.layers.pro.reasoning.confidence import compute_confidence
        from src.layers.pro.reasoning.context_packer import pack_context

        provenance, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)

        # Build deterministic context preview from provenance source_refs (MVP)
        context_preview, _ = pack_context(
            preview_items,
            max_chars=int(getattr(request, "max_context_chars", 12000)),
        )

        from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt

        fallback_reason = None

        if self.llm is not None:
            prompt = build_reasoning_prompt(
                request,
                context_preview=context_preview,
                provenance=provenance,
            )
            # Minimal LLM contract: async generate(prompt: str) -> str
            import asyncio

            try:
                answer_text = await asyncio.wait_for(
                    self.llm.generate(prompt),
                    timeout=float(self.llm_timeout_s),
                )
            except asyncio.TimeoutError:
                fallback_reason = "timeout"
                # Fail-safe fallback (MVP): keep system responsive and deterministic
                answer_text = "(reasoning layer stub)"
            except Exception:
                fallback_reason = "error"
                # Fail-safe fallback (MVP): keep system responsive and deterministic
                answer_text = "(reasoning layer stub)"
        else:
            answer_text = "(reasoning layer stub)"

        # Emit structured log line (best-effort, non-fatal)
        try:
            from loguru import logger
            elapsed_ms = int((perf_counter() - t0) * 1000)
            logger.info(
                "reasoning.synthesize elapsed_ms={} llm_used={} fallback={} conf={} k={} depth={} chunks={} nodes={} edges={} qlen={}",
                elapsed_ms,
                bool(self.llm is not None),
                fallback_reason,
                float(compute_confidence(provenance)),
                int(getattr(request, 'k', 0) or 0),
                int(getattr(request, 'graph_depth', 0) or 0),
                len([c for c in used_chunks if c]),
                len([n for n in used_nodes if n]),
                len([e for e in used_edges if e]),
                len(str(getattr(request, 'query', '') or '')),
            )
        except Exception:
            pass

        return AnswerResponse(
            answer=answer_text,
            confidence=compute_confidence(provenance),
            context_preview=context_preview,
            provenance=provenance,
            used_chunks=[c for c in used_chunks if c],
            used_nodes=[n for n in used_nodes if n],
            used_edges=[e for e in used_edges if e],
        )

