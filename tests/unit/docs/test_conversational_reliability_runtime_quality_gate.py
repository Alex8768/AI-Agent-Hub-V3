from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_conversational_reliability_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/CONVERSATIONAL_RELIABILITY_RUNTIME.md")
    required_markers = [
        "`build_reasoning_response_style_runtime`",
        "`response_style.py`",
        "`normalize_low_evidence_friendliness`",
        "`conversational_runtime_parity`",
        "`assistant_low_evidence_friendliness_applied`",
        "`tests/unit/layers/pro/test_reasoning_kernel_runtime.py`",
        "`tests/unit/layers/pro/test_reasoning_response_style.py`",
        "`tests/unit/services/answer/test_answer_service_debug_snapshot.py`",
        "`tests/unit/api/test_answer_endpoint_debug_snapshot.py`",
        "`tests/unit/docs/test_conversational_reliability_runtime_quality_gate.py`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing conversational reliability marker: {marker}"


def test_conversational_reliability_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/CONVERSATIONAL_RELIABILITY_RUNTIME.md" in readme
    assert "Conversational reliability runtime docs quality gate" in roadmap

