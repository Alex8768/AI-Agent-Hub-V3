from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assistant_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/ASSISTANT_RUNTIME.md")
    required_markers = [
        "Assistant contract version: `v1`",
        "`strict_rag`",
        "`assistant_fallback`",
        "`draft_orchestration`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
        "`assistant_contract_version`",
        "`response_mode`",
        "`response_language`",
        "`anticipatory.draft_actions`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing assistant runtime marker: {marker}"


def test_assistant_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/ASSISTANT_RUNTIME.md" in readme
    assert "feature_assistant_mode" in roadmap
    assert "feature_assistant_proactive" in roadmap
    assert "feature_assistant_actions" in roadmap
