from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    # Similarity threshold (applies to items that have 'score')
    similarity_threshold: float = 0.0

    # Max evidence items after filtering/dedupe/rerank/budget
    max_evidence: int = 50

    # Dedupe by (type, id)
    dedupe: bool = True

    # Deterministic rerank (score/confidence/type/id)
    rerank: bool = True

    # Source budgets (post-rerank). Use None to disable a budget.
    max_chunks: int | None = None
    max_memory: int | None = None
    max_edges: int | None = None


def _dedupe_type_id(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        t = str(it.get("type") or "")
        i = str(it.get("id") or "")
        if not t or not i:
            continue
        key = (t, i)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def deterministic_rerank(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic rerank for evidence items.

    Strategy (stable, 2026-friendly):
      1) score desc (missing -> -inf)
      2) confidence desc (missing -> -inf)
      3) type priority: chunk > memory > node > edge > other
      4) id asc (stable tie-break)

    This ensures repeatable ordering across runs and platforms.
    """

    def _score(v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return float("-inf")

    def _type_rank(t: str) -> int:
        # smaller is better
        if t == "chunk":
            return 0
        if t == "memory":
            return 1
        if t == "node":
            return 2
        if t == "edge":
            return 3
        return 9

    def key(it: dict[str, Any]):
        t = str(it.get("type") or "")
        i = str(it.get("id") or "")
        sc = _score(it.get("score", None))
        cf = _score(it.get("confidence", None))
        tr = _type_rank(t)
        # python sorts ascending; we want score/confidence descending
        return (-sc, -cf, tr, i)

    return sorted(list(items or []), key=key)


def _apply_source_budgets(
    items: list[dict[str, Any]],
    *,
    max_chunks: int | None,
    max_memory: int | None,
    max_edges: int | None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Select evidence items respecting per-source budgets.

    Budgets apply to types:
      - chunk
      - memory
      - edge
    Other types are unlimited (but still subject to overall clamp later).
    """
    used = {"chunks": 0, "memory": 0, "edges": 0}

    def _allow(t: str) -> bool:
        if t == "chunk":
            return max_chunks is None or used["chunks"] < int(max_chunks)
        if t == "memory":
            return max_memory is None or used["memory"] < int(max_memory)
        if t == "edge":
            return max_edges is None or used["edges"] < int(max_edges)
        return True

    out: list[dict[str, Any]] = []
    for it in items or []:
        t = str(it.get("type") or "")
        if not _allow(t):
            continue
        out.append(it)
        if t == "chunk":
            used["chunks"] += 1
        elif t == "memory":
            used["memory"] += 1
        elif t == "edge":
            used["edges"] += 1

    return out, used


def apply_policy(
    evidence: list[dict[str, Any]],
    *,
    policy: RetrievalPolicy,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply retrieval quality policy to evidence items.

    Evidence items are dict-like with keys:
      - type: str
      - id: str
      - optional score: float
      - optional confidence: float

    Returns (filtered_evidence, stats).
    """
    stats: dict[str, Any] = {
        "evidence_total_before_policy": int(len(evidence or [])),
        "similarity_threshold": float(policy.similarity_threshold),
        "dedupe_applied": bool(policy.dedupe),
        "rerank_applied": bool(policy.rerank),
        "rerank_strategy": "score_confidence_type_id" if policy.rerank else "none",
        "budget_applied": any(v is not None for v in (policy.max_chunks, policy.max_memory, policy.max_edges)),
    }

    items = list(evidence or [])

    # Filter by similarity score if present (only for items with score)
    if policy.similarity_threshold is not None:
        thr = float(policy.similarity_threshold)
        filtered: list[dict[str, Any]] = []
        for it in items:
            sc = it.get("score", None)
            if sc is None:
                filtered.append(it)
                continue
            try:
                if float(sc) >= thr:
                    filtered.append(it)
            except Exception:
                filtered.append(it)
        items = filtered

    stats["evidence_after_filter_count"] = int(len(items))

    # Dedupe
    if policy.dedupe:
        items = _dedupe_type_id(items)

    stats["evidence_after_dedupe_count"] = int(len(items))

    # Deterministic rerank (after filtering/dedupe, before budget/clamp)
    if policy.rerank:
        items = deterministic_rerank(items)

    stats["evidence_after_rerank_count"] = int(len(items))

    # Source balancing budgets (post-rerank)
    if stats["budget_applied"]:
        items, used = _apply_source_budgets(
            items,
            max_chunks=policy.max_chunks,
            max_memory=policy.max_memory,
            max_edges=policy.max_edges,
        )
        stats["budget_chunks_used"] = int(used["chunks"])
        stats["budget_memory_used"] = int(used["memory"])
        stats["budget_edges_used"] = int(used["edges"])

    stats["evidence_after_budget_count"] = int(len(items))

    # Clamp overall
    if policy.max_evidence is not None and int(policy.max_evidence) > 0:
        items = items[: int(policy.max_evidence)]

    stats["evidence_after_policy_count"] = int(len(items))
    return items, stats
