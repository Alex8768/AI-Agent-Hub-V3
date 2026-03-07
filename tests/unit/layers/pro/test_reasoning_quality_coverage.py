from __future__ import annotations

from src.layers.pro.reasoning.contracts import ProvenanceItem
from src.layers.pro.reasoning.quality_coverage import score_claim_coverage


def test_score_claim_coverage_empty_claims_returns_zero_shape():
    result = score_claim_coverage(claims=[], provenance=[])
    assert result == {
        "claims_total": 0,
        "claims_covered": 0,
        "claims_uncovered": 0,
        "coverage_score": 0.0,
        "covered_claim_indices": [],
        "uncovered_claim_indices": [],
    }


def test_score_claim_coverage_counts_covered_and_uncovered_claims():
    claims = [
        "Vector retrieval uses source refs from document chunks",
        "Graph traversal adds supporting node context",
    ]
    provenance = [
        ProvenanceItem(
            type="chunk",
            id="c1",
            source_refs=["doc:handbook#1"],
            meta={"snippet": "document chunks are indexed by vector retrieval"},
        ),
        ProvenanceItem(
            type="node",
            id="n1",
            meta={"text": "entity relation in graph"},
        ),
    ]
    result = score_claim_coverage(claims=claims, provenance=provenance, min_overlap_tokens=2)
    assert result["claims_total"] == 2
    assert result["claims_covered"] == 1
    assert result["claims_uncovered"] == 1
    assert result["coverage_score"] == 0.5
    assert result["covered_claim_indices"] == [0]
    assert result["uncovered_claim_indices"] == [1]


def test_score_claim_coverage_uses_meta_content_and_min_overlap_floor():
    claims = ["Quality confidence relies on evidence coverage"]
    provenance = [
        ProvenanceItem(
            type="chunk",
            id="c1",
            meta={"content": "evidence coverage"},
        ),
    ]
    result = score_claim_coverage(claims=claims, provenance=provenance, min_overlap_tokens=0)
    assert result["claims_covered"] == 1
    assert result["coverage_score"] == 1.0
