from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    # Similarity threshold (applies to items that have 'score')
    similarity_threshold: float = 0.0

    # Max evidence items after filtering/dedupe
    max_evidence: int = 50

    # Dedupe by (type, id)
    dedupe: bool = True


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

    # Clamp
    if policy.max_evidence is not None and int(policy.max_evidence) > 0:
        items = items[: int(policy.max_evidence)]

    stats["evidence_after_policy_count"] = int(len(items))
    return items, stats
