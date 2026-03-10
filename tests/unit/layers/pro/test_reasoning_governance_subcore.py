from __future__ import annotations


def test_build_governance_subcore_bundle_marks_trace_and_receipt():
    from src.layers.pro.reasoning.governance.subcore import build_governance_subcore_bundle

    out = build_governance_subcore_bundle(
        reasoning_trace={"query": "x", "answer": "y"},
        reasoning_timeline={"events": [{"name": "step"}], "total_duration_ms": 3},
        execution_receipt={"status": "ready"},
    )

    assert out.get("contract_version") == "v1"
    assert out.get("mode") == "governance_subcore"
    assert out.get("status") == "ready"
    assert out.get("trace_status") == "present"
    assert out.get("timeline_status") == "present"
    assert out.get("receipt_status") == "ready"
    assert out.get("replay_status") == "available_via_receipt"
    reason_codes = list(out.get("reason_codes") or [])
    assert "governance_subcore_runtime_wired" in reason_codes
    assert "governance_subcore_trace_present" in reason_codes
    assert "governance_subcore_timeline_present" in reason_codes
    assert "governance_subcore_receipt_active" in reason_codes
