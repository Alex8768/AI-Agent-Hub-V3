from __future__ import annotations

import json
import re
from typing import Any, Optional

from src.core.config import settings
from src.core.types import Message, MessageRole
from src.layers.base.llm.providers import get_llm_provider

from src.layers.pro.graph_rag.contracts.extraction import ExtractionResult, SourceRef


SYSTEM_PROMPT = """You are an information extraction engine.
Return ONLY valid JSON matching this schema:

{
  "entities": [
    {
      "node_type": "person|org|product|concept|place|event|other",
      "name": "string",
      "aliases": ["string"],
      "attributes": { "string": "any" },
      "confidence": 0.0-1.0,
      "source_ref": { "document_id": "string", "chunk_id": "string", "snippet": "string<=240" }
    }
  ],
  "relations": [
    {
      "rel_type": "mentions|related_to|works_at|owns|uses|located_in|other",
      "src_name": "string",
      "src_type": "person|org|product|concept|place|event|other",
      "dst_name": "string",
      "dst_type": "person|org|product|concept|place|event|other",
      "attributes": { "string": "any" },
      "confidence": 0.0-1.0,
      "source_ref": { "document_id": "string", "chunk_id": "string", "snippet": "string<=240" }
    }
  ],
  "notes": "optional",
  "errors": []
}

Rules:
- Output JSON only. No markdown. No extra keys.
- Use short snippet (<=240 chars) that supports the entity/relation.
- confidence must be set for every item.
- Limit entities <= 20, relations <= 30.
"""


def _extract_json(text: str) -> str:
    """Best-effort extraction of a JSON object from model output."""
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in output")
    return m.group(0)


async def extract_from_chunk(
    *,
    workspace_id: str,
    document_id: str,
    chunk_id: str,
    text: str,
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 800,
) -> ExtractionResult:
    provider = await get_llm_provider(provider_type=provider_type or settings.llm_provider)

    user_prompt = (
        f"workspace_id={workspace_id}\n"
        f"document_id={document_id}\n"
        f"chunk_id={chunk_id}\n\n"
        f"TEXT:\n{text}\n"
    )

    cfg: dict[str, Any] = {"temperature": temperature, "max_tokens": max_tokens}
    if model:
        cfg["model"] = model

    completion = await provider.complete(
        messages=[
            Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=MessageRole.USER, content=user_prompt),
        ],
        config=cfg,
    )

    raw = completion.content or ""
    try:
        payload = json.loads(_extract_json(raw))
        # Fill missing source_ref if model omitted it (rare) — enforce UI-ready provenance
        res = ExtractionResult.model_validate(payload)
        for e in res.entities:
            if not e.source_ref:
                e.source_ref = SourceRef(document_id=document_id, chunk_id=chunk_id, snippet=(text[:240]))
        for r in res.relations:
            if not r.source_ref:
                r.source_ref = SourceRef(document_id=document_id, chunk_id=chunk_id, snippet=(text[:240]))
        return res
    except Exception as e:
        return ExtractionResult(entities=[], relations=[], errors=[f"extract_parse_error: {type(e).__name__}: {e}"])
