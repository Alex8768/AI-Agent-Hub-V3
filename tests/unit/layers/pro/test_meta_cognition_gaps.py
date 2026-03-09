from __future__ import annotations

from src.layers.pro.meta_cognition.gaps import build_gap_map, build_knowledge_gap


def test_build_knowledge_gap_normalizes_fields() -> None:
    gap = build_knowledge_gap(
        gap_id="",
        topic="  Revenue forecast ",
        gap_type="LOW_CONFIDENCE",
        confidence=1.2,
        evidence_refs=["doc:2", "doc:1", "doc:2"],
        source=" verify ",
        message="  weak support ",
    )
    assert gap == {
        "gap_id": "low_confidence:revenue forecast",
        "topic": "Revenue forecast",
        "gap_type": "low_confidence",
        "confidence": 1.0,
        "evidence_refs": ["doc:1", "doc:2"],
        "source": "verify",
        "message": "weak support",
    }


def test_build_gap_map_is_deterministic() -> None:
    gaps = [
        {"topic": "A", "gap_type": "missing_data", "confidence": 0.9, "gap_id": "g2"},
        {"topic": "B", "gap_type": "contradiction", "confidence": 0.2, "gap_id": "g1"},
    ]
    map_a = build_gap_map(session_id="s1", gaps=gaps)
    map_b = build_gap_map(session_id="s1", gaps=list(reversed(gaps)))
    assert map_a == map_b
    assert map_a["status"] == "needs_attention"
    assert map_a["total_gaps"] == 2
    assert map_a["high_priority_gaps"] == 1


def test_build_gap_map_clear_status_with_no_gaps() -> None:
    gap_map = build_gap_map(session_id="s2", gaps=[])
    assert gap_map == {
        "session_id": "s2",
        "status": "clear",
        "total_gaps": 0,
        "high_priority_gaps": 0,
        "coverage_score": 1.0,
        "gaps": [],
        "reason_codes": [],
        "warnings": [],
    }
