from __future__ import annotations

import pytest

from src.layers.pro.reasoning.contracts import (
    AnswerRequest,
    AnswerResponse,
    ProvenanceItem,
)


def test_answer_request_defaults():
    req = AnswerRequest(query="What is X?")
    assert req.k == 8
    assert req.graph_depth == 1
    assert req.max_context_chars == 12000
    assert req.filters == {}


def test_answer_request_validation():
    with pytest.raises(Exception):
        AnswerRequest(query="")  # empty query invalid

    with pytest.raises(Exception):
        AnswerRequest(query="q", k=0)

    with pytest.raises(Exception):
        AnswerRequest(query="q", graph_depth=5)


def test_provenance_item_basic():
    p = ProvenanceItem(type="chunk", id="c1")
    assert p.type == "chunk"
    assert p.id == "c1"
    assert p.source_refs == []
    assert p.meta == {}
    assert p.origin == "unknown"
    assert p.reliability is None


def test_answer_response_confidence_bounds():
    with pytest.raises(Exception):
        AnswerResponse(answer="a", confidence=1.5)

    resp = AnswerResponse(answer="a", confidence=0.8)
    assert resp.answer == "a"
    assert resp.confidence == 0.8
    assert resp.provenance == []


def test_provenance_item_origin_and_reliability_validation():
    p = ProvenanceItem(type="memory", id="m1", origin="memory", reliability=0.9)
    assert p.origin == "memory"
    assert p.reliability == 0.9

    with pytest.raises(Exception):
        ProvenanceItem(type="chunk", id="c2", reliability=1.2)
