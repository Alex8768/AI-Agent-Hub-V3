from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_debt_resolution_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/DEBT_RESOLUTION_RUNTIME.md")
    required_markers = [
        "`TD-A2.45-001`",
        "`TD-A2.45-003`",
        "`TD-A2.45-004`",
        "`_run_assistant_execution_orchestration_seam`",
        "`_build_memory_consistency_strategy_contract`",
        "`memory_consistency_strategy`",
        "`run_utf8.py`",
        "`src.api.main:app`",
        "`tests/unit/docs/test_debt_resolution_runtime_quality_gate.py`",
        "`tests/unit/core/test_runtime_entrypoint_compat_runner.py`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing debt resolution runtime marker: {marker}"


def test_debt_resolution_runtime_quality_gate_registry_and_references():
    registry = _read("docs/development/TECHNICAL_DEBT_REGISTRY.md")
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "resolved_in_a2_47" in registry
    assert "docs/architecture/DEBT_RESOLUTION_RUNTIME.md" in readme
    assert "Debt resolution runtime docs quality gate" in roadmap
