from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_feedback_learning_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/FEEDBACK_LEARNING_RUNTIME.md")
    required_markers = [
        "Feedback contract version: `v1`",
        "Plan contract version: `v1`",
        "`feedback_contract_version`",
        "`assistant_feedback_learning`",
        "`feedback_policy`",
        "`assistant_plan`",
        "`feedback_policy_forced_fallback`",
        "`feedback_signals_exceed_max`",
        "`feedback_latest_signal_mismatch`",
        "`feedback_runtime_wired`",
        "`feedback_runtime_unknown_signals_removed`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing feedback learning runtime marker: {marker}"


def test_feedback_learning_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/FEEDBACK_LEARNING_RUNTIME.md" in readme
    assert "Feedback learning runtime docs quality gate" in roadmap
