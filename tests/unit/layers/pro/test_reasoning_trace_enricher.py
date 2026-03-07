from __future__ import annotations

from src.layers.pro.reasoning.trace.trace_enricher import enrich_reasoning_trace_with_timeline


def test_enrich_reasoning_trace_with_timeline_attaches_normalized_timeline():
    trace = {
        "query": "Q",
        "plan": ["p1"],
        "steps": ["s1"],
        "verify_results": [{"status": "pass", "reasons": []}],
        "quality": {"confidence": 0.8},
        "answer": "A",
    }
    timeline = {
        "events": [
            {"event_type": " planner ", "step_index": 0, "started_at_ms": 2, "ended_at_ms": 6}
        ]
    }
    enriched = enrich_reasoning_trace_with_timeline(trace=trace, timeline=timeline)
    assert enriched["query"] == "Q"
    assert enriched["timeline"] == {
        "events": [
            {
                "event_type": "planner",
                "step_index": 0,
                "started_at_ms": 2,
                "ended_at_ms": 6,
                "duration_ms": 4,
                "status": "",
                "metadata": {},
            }
        ],
        "total_duration_ms": 4,
    }


def test_enrich_reasoning_trace_with_timeline_keeps_empty_timeline_stable():
    enriched = enrich_reasoning_trace_with_timeline(
        trace={"query": "", "plan": [], "steps": [], "verify_results": [], "quality": {}, "answer": ""},
        timeline={},
    )
    assert enriched["timeline"] == {"events": [], "total_duration_ms": 0}
