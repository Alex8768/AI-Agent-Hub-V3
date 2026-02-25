from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro).

    This is an intentionally minimal skeleton.
    Retrieval remains in HybridRetriever; this layer will:
      - expand graph strategically (policy-driven)
      - aggregate evidence (chunks/nodes/edges)
      - pack bounded context (budget + dedupe + ranking)
      - synthesize answer via LLM
      - return answer + provenance + confidence
    """

    # NOTE: real dependencies will be injected later (schema-first, tests-first).
    def __init__(self) -> None:
        # Keep init side-effect free.
        pass
