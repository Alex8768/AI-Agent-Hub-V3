from __future__ import annotations

from typing import Any

from src.layers.pro.reasoning.contracts import ProvenanceItem


def _default_origin_for_type(tp: str) -> str:
    t = str(tp or "").lower()
    if t == "chunk":
        return "vector"
    if t in {"node", "edge"}:
        return "graph"
    if t == "memory":
        return "memory"
    return "unknown"


def normalize_retrieval_result(
    result: Any,
) -> tuple[list[ProvenanceItem], list[str], list[str], list[str], list[str]]:
    """Normalize retriever output into domain evidence structures.

    Accepts a best-effort dict shape:
      {
        "results": [{"chunk_id": ...}, ...],
        "graph": {"nodes": [{"id": ...}], "edges": [{"id": ...}]},
        "evidence": [{"type": "...", "id": "...", "source_refs": [...], ...}, ...]
      }

    Returns:
      (provenance, used_chunks, used_nodes, used_edges, preview_items)

    preview_items are derived from provenance.source_refs (flattened).
    """
    provenance_raw: list[dict[str, Any]] = []
    used_chunks: list[str] = []
    used_nodes: list[str] = []
    used_edges: list[str] = []

    if isinstance(result, dict):
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
        used_chunks = [r.get("chunk_id") for r in res if isinstance(r, dict) and r.get("chunk_id")]

    provenance: list[ProvenanceItem] = []
    for p in provenance_raw:
        try:
            item = dict(p)
            item.setdefault("origin", _default_origin_for_type(item.get("type", "")))
            if item.get("reliability") is None and item.get("confidence") is not None:
                item["reliability"] = item.get("confidence")
            provenance.append(ProvenanceItem.model_validate(item))
        except Exception:
            continue

    preview_items: list[str] = []
    for p in provenance:
        preview_items.extend([s for s in p.source_refs if s])

    return (
        provenance,
        [c for c in used_chunks if c],
        [n for n in used_nodes if n],
        [e for e in used_edges if e],
        preview_items,
    )
