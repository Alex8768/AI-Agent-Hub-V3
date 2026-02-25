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

    async def synthesize(self, request):
        """Synthesize an answer from retrieval evidence.

        MVP: orchestration only (no LLM yet).
        - Calls injected retriever
        - Pass-through provenance (best-effort) if retriever provides it
        - Returns deterministic stub answer
        """
        result = await self.retriever.retrieve(request)

        provenance_raw = []
        used_chunks: list[str] = []
        used_nodes: list[str] = []
        used_edges: list[str] = []

        if isinstance(result, dict):
            # Accept common hybrid shape: {results, graph, evidence}
            evid = result.get("evidence") or []
            for item in evid:
                if isinstance(item, dict) and "type" in item and "id" in item:
                    provenance_raw.append(item)

            g = result.get("graph") or {}
            nodes = g.get("nodes") or []
            edges = g.get("edges") or []
            used_nodes = [n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")]
            used_edges = [e.get("id") for e in edges if isinstance(e, dict) and e.get("id")]

            res = result.get("results") or []
            # If SearchResult contains chunk_id, collect it (best-effort)
            used_chunks = [r.get("chunk_id") for r in res if isinstance(r, dict) and r.get("chunk_id")]

        from src.layers.pro.reasoning.contracts import AnswerResponse, ProvenanceItem
        from src.layers.pro.reasoning.confidence import compute_confidence
        from src.layers.pro.reasoning.context_packer import pack_context

        provenance = []
        for p in provenance_raw:
            try:
                provenance.append(ProvenanceItem.model_validate(p))
            except Exception:
                # ignore malformed provenance
                continue

        # Build deterministic context preview from provenance source_refs (MVP)
        preview_items: list[str] = []
        for p in provenance:
            preview_items.extend([s for s in p.source_refs if s])
        context_preview, _ = pack_context(preview_items, max_chars=int(getattr(request, 'max_context_chars', 12000)))

        return AnswerResponse(
            answer="(reasoning layer stub)",
            confidence=compute_confidence(provenance),
            context_preview=context_preview,
            provenance=provenance,
            used_chunks=[c for c in used_chunks if c],
            used_nodes=[n for n in used_nodes if n],
            used_edges=[e for e in used_edges if e],
        )

