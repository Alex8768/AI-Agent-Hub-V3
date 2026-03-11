from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_operational_guardrails_quality_gate_kpi_and_mapping_markers():
    content = _read("docs/development/PROJECT_ANCHOR.md")
    required_markers = [
        "`healthy_request_kpi`",
        "`fallback_rate_kpi`",
        "`soft_failure_rate_kpi`",
        "`requests_with_soft_failures`",
        "`requests_with_fallback`",
        '`response_mode == "assistant_fallback"`',
        "`planning_reason_codes`",
        "`soft_failures_count`",
        "`fallback_count`",
        "`warning`",
        "`critical`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing A2.56 KPI policy marker: {marker}"


def test_operational_guardrails_quality_gate_docs_sync_markers():
    status = _read("docs/development/STATUS.md")
    checklist = _read("docs/development/PROJECT_CHECKLIST.md")
    features = _read("docs/architecture/PLATFORM_FEATURES.md")

    assert (
        "A2.56 patch 4 complete" in status
        or "Anchor Closed — A2.56 complete" in status
        or "Post-A2.56 Maintenance — M1 complete" in status
    ), "Missing A2.56 status marker (patch 4 progress, closure, or maintenance)"
    assert "[x] Patch 4 — guardrail test/policy enforcement hardening" in checklist
    assert "A2.56 operational KPI policy quality-gate enforcement (patch 4)" in features
