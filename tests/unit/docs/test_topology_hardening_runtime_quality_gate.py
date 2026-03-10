from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_topology_hardening_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/TOPOLOGY_HARDENING_RUNTIME.md")
    required_markers = [
        "`kernel/`",
        "`governance/`",
        "`extensions/`",
        "`execution_plane/`",
        "`build_reasoning_kernel`",
        "`build_governance_subcore_bundle`",
        "`normalize_execution_request`",
        "`build_execution_request_boundary_bundle`",
        "`execution_request_boundary`",
        "`kernel -> execution_plane`",
        "`governance -> interface`",
        "`tests/unit/layers/pro/test_reasoning_topology_dependency_quality_gate.py`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing topology hardening marker: {marker}"


def test_topology_hardening_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/TOPOLOGY_HARDENING_RUNTIME.md" in readme
    assert "Topology hardening runtime docs quality gate" in roadmap
