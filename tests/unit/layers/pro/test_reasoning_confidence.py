from __future__ import annotations

from src.layers.pro.reasoning.confidence import clamp01, compute_confidence
from src.layers.pro.reasoning.contracts import ProvenanceItem


def test_confidence_no_provenance_is_zero():
    assert compute_confidence([]) == 0.0


def test_confidence_no_item_confidences_defaults_to_point_two():
    prov = [ProvenanceItem(type="chunk", id="c1"), ProvenanceItem(type="node", id="n1")]
    assert compute_confidence(prov) == 0.2


def test_confidence_average():
    prov = [
        ProvenanceItem(type="chunk", id="c1", confidence=0.9),
        ProvenanceItem(type="edge", id="e1", confidence=0.1),
    ]
    assert compute_confidence(prov) == 0.5


def test_clamp01_bounds():
    assert clamp01(-1.0) == 0.0
    assert clamp01(2.0) == 1.0
