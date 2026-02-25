from __future__ import annotations

from src.layers.pro.reasoning.contracts import AnswerRequest, ProvenanceItem


_SYSTEM_RULES = """You are a careful assistant.
Use ONLY the provided context.
If the context is insufficient, say you don't know.
Cite evidence by referencing source_refs when available.
Be concise and precise.
"""


def build_reasoning_prompt(
    request: AnswerRequest,
    *,
    context_preview: str,
    provenance: list[ProvenanceItem] | None = None,
) -> str:
    """Build a deterministic prompt for answer synthesis (MVP).

    Domain-level (no API coupling).
    """
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
        f"Question: {request.query}",
        "",
        "Context:",
        (context_preview or "(empty)").strip(),
    ]

    if prov_block:
        parts.extend(["", "Provenance:", prov_block])

    parts.extend(["", "Answer:"])
    return "\n".join(parts).strip() + "\n"
