from __future__ import annotations

import hashlib
import re
from typing import Any

from src.core.providers import get_graph_store
from src.layers.pro.graph_rag.contracts.extraction import ExtractionResult
from src.layers.pro.graph_rag.extractors.llm_extractor import extract_from_chunk


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9а-яё]+", "-", s, flags=re.IGNORECASE)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:80] if s else "x"


def _hid(*parts: str, n: int = 10) -> str:
    h = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()
    return h[:n]


def make_node_id(node_type: str, name: str) -> str:
    base = f"{node_type}:{_slug(name)}"
    return f"{base}:{_hid(node_type, name)}"


def make_edge_id(rel_type: str, src_id: str, dst_id: str) -> str:
    # stable per relation pair (idempotent)
    return f"{rel_type}:{src_id}->{dst_id}"


async def process_chunk(
    *,
    workspace_id: str,
    document_id: str,
    chunk_id: str,
    text: str,
) -> dict[str, Any]:
    gs = get_graph_store()
    if gs is None:
        return {"status": "disabled", "reason": "feature_graphrag is off"}

    extraction: ExtractionResult = await extract_from_chunk(
        workspace_id=workspace_id,
        document_id=document_id,
        chunk_id=chunk_id,
        text=text,
    )

    if extraction.errors:
        return {"status": "error", "errors": extraction.errors, "entities": 0, "relations": 0}

    # Upsert entities
    name_to_node: dict[tuple[str, str], str] = {}
    for ent in extraction.entities[:20]:
        nid = make_node_id(ent.node_type, ent.name)
        name_to_node[(ent.node_type, ent.name)] = nid

        meta = {
            "confidence": ent.confidence,
            "aliases": ent.aliases,
            "attributes": ent.attributes,
            "source_refs": [ent.source_ref.model_dump()],
        }
        await gs.upsert_node(
            workspace_id=workspace_id,
            node_id=nid,
            node_type=ent.node_type,
            name=ent.name,
            metadata=meta,
        )

    # Upsert relations
    rel_count = 0
    for rel in extraction.relations[:30]:
        src_id = name_to_node.get((rel.src_type, rel.src_name)) or make_node_id(rel.src_type, rel.src_name)
        dst_id = name_to_node.get((rel.dst_type, rel.dst_name)) or make_node_id(rel.dst_type, rel.dst_name)

        # ensure nodes exist
        if (rel.src_type, rel.src_name) not in name_to_node:
            await gs.upsert_node(
                workspace_id=workspace_id,
                node_id=src_id,
                node_type=rel.src_type,
                name=rel.src_name,
                metadata={"confidence": rel.confidence, "source_refs": [rel.source_ref.model_dump()]},
            )
        if (rel.dst_type, rel.dst_name) not in name_to_node:
            await gs.upsert_node(
                workspace_id=workspace_id,
                node_id=dst_id,
                node_type=rel.dst_type,
                name=rel.dst_name,
                metadata={"confidence": rel.confidence, "source_refs": [rel.source_ref.model_dump()]},
            )

        eid = make_edge_id(rel.rel_type, src_id, dst_id)
        meta = {
            "confidence": rel.confidence,
            "attributes": rel.attributes,
            "source_refs": [rel.source_ref.model_dump()],
        }
        await gs.upsert_edge(
            workspace_id=workspace_id,
            edge_id=eid,
            src_id=src_id,
            dst_id=dst_id,
            rel_type=rel.rel_type,
            metadata=meta,
        )
        rel_count += 1

    return {"status": "ok", "entities": len(extraction.entities[:20]), "relations": rel_count}
