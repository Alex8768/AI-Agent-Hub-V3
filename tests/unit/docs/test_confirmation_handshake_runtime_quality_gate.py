from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_confirmation_handshake_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/CONFIRMATION_HANDSHAKE_RUNTIME.md")
    required_markers = [
        "Handshake contract version: `v1`",
        "Execution receipt contract version: `v1`",
        "`assistant_execution_handshake`",
        "`execution_transition_policy`",
        "`assistant_execution_receipt`",
        "`pending_confirmation`",
        "`approved`",
        "`cancelled`",
        "`handshake_decision`",
        "`handshake_confirmation_token`",
        "`handshake_action_ids`",
        "`confirmation_guarded`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing confirmation runtime marker: {marker}"


def test_confirmation_handshake_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/CONFIRMATION_HANDSHAKE_RUNTIME.md" in readme
    assert "Confirmation handshake runtime docs quality gate" in roadmap
