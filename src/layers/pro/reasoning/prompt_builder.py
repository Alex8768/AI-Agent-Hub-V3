from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest, ProvenanceItem
from src.layers.pro.reasoning.kernel import normalize_reasoning_query_input


_SYSTEM_RULES = """You are a careful assistant.
Use ONLY the provided context.
Always respond in the same language as the user's question.
If the context is insufficient, say you don't know in the same language as the user's question.
Cite evidence by referencing source_refs when available.
Be concise and precise.
"""

def build_reasoning_prompt(
    query: str | AnswerRequest,
    context_preview: str,
    provenance: list[ProvenanceItem] | None = None,
    instruction: str | None = None,
) -> str:
    """Build a deterministic prompt for answer synthesis (MVP).

    Args:
        query: query string or AnswerRequest object
        context_preview: packed context preview
        provenance: list of provenance items
        instruction: optional custom instruction (for agent nodes)
    """
    query_text = normalize_reasoning_query_input(query)

    prov_lines: list[str] = []
    if provenance:
        # Deterministic order: as provided
        for p in provenance:
            if not p.source_refs:
                continue
            # Keep it short: type/id + first few refs
            refs = ", ".join(p.source_refs[:5])
            prov_lines.append(f"- {p.type}:{p.id} -> {refs}")

    prov_block = "\n".join(prov_lines).strip()

    parts: list[str] = [
        _SYSTEM_RULES.strip(),
        "",
        f"Question: {query_text}",
        "",
        "Context:",
        (context_preview or "(empty)").strip(),
    ]

    if prov_block:
        parts.extend(["", "Provenance:", prov_block])

    if instruction:
        parts.extend(["", "Instruction:", instruction])

    parts.extend(["", "Answer:"])
    return "\n".join(parts).strip() + "\n"
