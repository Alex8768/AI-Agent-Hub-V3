from __future__ import annotations

from src.layers.pro.reasoning.quality_claims import extract_claims


def test_extract_claims_empty_input_returns_empty_list():
    assert extract_claims(reasoning_output="") == []
    assert extract_claims(reasoning_output="   ") == []


def test_extract_claims_from_mixed_lines_and_sentences():
    text = """
    - The system uses evidence from vector retrieval.
    - The system uses evidence from vector retrieval.
    1. Graph edges are used to expand context for reasoning.
    Final answer quality depends on evidence coverage. Confidence should remain deterministic.
    """
    claims = extract_claims(reasoning_output=text, max_claims=8, min_claim_chars=12)
    assert claims == [
        "The system uses evidence from vector retrieval.",
        "Graph edges are used to expand context for reasoning.",
        "Final answer quality depends on evidence coverage.",
        "Confidence should remain deterministic.",
    ]


def test_extract_claims_applies_limit_and_filters_short_fragments():
    text = "Ok. A2. Good result from verify step. Another strong claim for confidence model."
    claims = extract_claims(reasoning_output=text, max_claims=1, min_claim_chars=12)
    assert claims == ["Good result from verify step."]


def test_extract_claims_non_positive_bounds_return_empty():
    text = "Reasoning claim that normally would pass."
    assert extract_claims(reasoning_output=text, max_claims=0) == []
    assert extract_claims(reasoning_output=text, min_claim_chars=0) == []
