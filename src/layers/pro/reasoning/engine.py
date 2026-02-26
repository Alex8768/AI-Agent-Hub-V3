from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro).

    Orchestration layer above retrieval (HybridRetriever-compatible).
    Architecture rules:
      - dependency injection for retriever/llm
      - no side effects in __init__
      - schema-first contracts in reasoning.contracts
    """

    retriever: object
    llm: object | None = None
    llm_timeout_s: float = 15.0

    async def synthesize(self, request):
        """Synthesize an answer from retrieval evidence.

        - Calls injected retriever
        - Normalizes evidence into provenance + packed context preview
        - If llm provided -> calls llm.generate(prompt) with timeout
        - Else if dry-run enabled -> deterministic pseudo-answer from context
        - Else -> deterministic stub answer
        """
        from time import perf_counter
        t0 = perf_counter()
        result = await self.retriever.retrieve(request)

        from src.layers.pro.reasoning.contracts import AnswerResponse
        from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
        from src.layers.pro.reasoning.confidence import compute_confidence
        from src.layers.pro.reasoning.context_packer import pack_context
        from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt
        from src.core.config import get_settings

        provenance, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)

        # Build deterministic context preview from provenance source_refs (UI-friendly)
        context_preview, _ = pack_context(
            preview_items,
            max_chars=int(getattr(request, "max_context_chars", 12000)),
        )

        s = get_settings()
        dry_run = bool(getattr(s, "feature_reasoning_llm_dry_run", False))

        fallback_reason: str | None = None

        if self.llm is not None:
            prompt = build_reasoning_prompt(
                request,
                context_preview=context_preview,
                provenance=provenance,
            )
            import asyncio

            try:
                answer_text = await asyncio.wait_for(
                    self.llm.generate(prompt),
                    timeout=float(self.llm_timeout_s),
                )
            except asyncio.TimeoutError:
                fallback_reason = "timeout"
                answer_text = "(reasoning layer stub)"
            except Exception:
                fallback_reason = "error"
                answer_text = "(reasoning layer stub)"
        else:
            if dry_run:
                fallback_reason = "dry_run"
                # Deterministic pseudo-answer: short summary + evidence ids
                ids = []
                for p in provenance[:5]:
                    try:
                        ids.append(f"{p.type}:{p.id}")
                    except Exception:
                        continue

                snippet = (context_preview or "").strip()
                if len(snippet) > 400:
                    snippet = snippet[:400].rstrip() + "…"

                parts = []
                if snippet:
                    parts.append("Draft answer (dry-run):")
                    parts.append(snippet)
                else:
                    parts.append("Draft answer (dry-run): (no context)")

                if ids:
                    parts.append("")
                    parts.append("Evidence:")
                    for x in ids:
                        parts.append(f"- {x}")

                answer_text = "\n".join(parts)
            else:
                answer_text = "(reasoning layer stub)"

        # Emit structured log line (best-effort)
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

        resp = AnswerResponse(
            answer=answer_text,
            confidence=compute_confidence(provenance),
            context_preview=context_preview,
            provenance=provenance,
            used_chunks=[c for c in used_chunks if c],
            used_nodes=[n for n in used_nodes if n],
            used_edges=[e for e in used_edges if e],
        )
        # Attach fallback reason for API layer (best-effort; diagnostics will carry it)
        try:
            setattr(resp, "_fallback_reason", fallback_reason)
        except Exception:
            pass
        return resp
