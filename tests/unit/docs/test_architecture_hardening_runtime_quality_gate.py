from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_architecture_hardening_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/ARCHITECTURE_HARDENING_RUNTIME.md")
    required_markers = [
        "Assistant contract version: `v1`",
        "Memory consistency contract version: `v1`",
        "`assistant_contract_version`",
        "`planning_reason_codes`",
        "`memory_consistency`",
        "`_build_answer_service_runtime_context`",
        "`_build_reasoning_runtime_adapter`",
        "`_build_memory_consistency_bundle`",
        "`memory_consistency_guard_evaluated`",
        "`memory_consistency_store_unavailable`",
        "`memory_consistency_session_hit`",
        "`memory_consistency_durable_approval_loaded`",
        "`memory_consistency_durable_idempotency_loaded`",
        "`docs/development/TECHNICAL_DEBT_REGISTRY.md`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing architecture hardening runtime marker: {marker}"


def test_architecture_hardening_runtime_quality_gate_debt_registry_markers():
    content = _read("docs/development/TECHNICAL_DEBT_REGISTRY.md")
    required_markers = [
        "# Technical Debt Registry",
        "`debt_id`",
        "`decision_status`",
        "`target_anchor`",
        "TD-A2.45-001",
        "TD-A2.45-002",
        "TD-A2.45-003",
        "TD-A2.45-004",
        "`run_utf8.py`",
        "`src.api.main:app`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing technical debt registry marker: {marker}"


def test_architecture_hardening_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/ARCHITECTURE_HARDENING_RUNTIME.md" in readme
    assert "docs/development/TECHNICAL_DEBT_REGISTRY.md" in readme
    assert "Architecture hardening runtime docs quality gate" in roadmap
