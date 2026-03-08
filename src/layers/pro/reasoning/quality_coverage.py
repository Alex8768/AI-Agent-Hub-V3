from __future__ import annotations

import re
from typing import Iterable

from src.layers.pro.reasoning.contracts import ProvenanceItem


_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def _iter_evidence_surfaces(provenance: Iterable[ProvenanceItem]) -> Iterable[str]:
    for item in provenance:
        parts: list[str] = [str(getattr(item, "id", "") or "")]
        parts.extend(str(x) for x in (getattr(item, "source_refs", []) or []))
        meta = dict(getattr(item, "meta", {}) or {})
        for key in ("title", "snippet", "text", "content"):
            value = meta.get(key)
            if value:
                parts.append(str(value))
        yield " ".join(p for p in parts if p)


def score_claim_coverage(
    *,
    claims: list[str],
    provenance: list[ProvenanceItem],
    min_overlap_tokens: int = 2,
) -> dict[str, object]:
    """Score deterministic claim-to-evidence lexical coverage.

    Coverage is considered positive for a claim when at least one evidence
    surface has token overlap above ``min_overlap_tokens``.
    """
    if min_overlap_tokens <= 0:
        min_overlap_tokens = 1

    cleaned_claims = [str(c or "").strip() for c in claims if str(c or "").strip()]
    if not cleaned_claims:
        return {
            "claims_total": 0,
            "claims_covered": 0,
            "claims_uncovered": 0,
            "coverage_score": 0.0,
            "covered_claim_indices": [],
            "uncovered_claim_indices": [],
        }

    evidence_tokens = [_tokenize(surface) for surface in _iter_evidence_surfaces(provenance)]
    covered_indices: list[int] = []
    uncovered_indices: list[int] = []

    for idx, claim in enumerate(cleaned_claims):
        claim_tokens = _tokenize(claim)
        is_covered = False
        if claim_tokens and evidence_tokens:
            for ev_tokens in evidence_tokens:
                overlap = len(claim_tokens.intersection(ev_tokens))
                if overlap >= min_overlap_tokens:
                    is_covered = True
                    break
        if is_covered:
            covered_indices.append(idx)
        else:
            uncovered_indices.append(idx)

    total = len(cleaned_claims)
    covered = len(covered_indices)
    score = float(covered / total) if total > 0 else 0.0
    return {
        "claims_total": total,
        "claims_covered": covered,
        "claims_uncovered": total - covered,
        "coverage_score": score,
        "covered_claim_indices": covered_indices,
        "uncovered_claim_indices": uncovered_indices,
    }
