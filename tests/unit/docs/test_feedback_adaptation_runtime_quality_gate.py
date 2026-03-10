from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_feedback_adaptation_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/FEEDBACK_ADAPTATION_RUNTIME.md")
    required_markers = [
        "Adaptation contract version: `v1`",
        "Feedback contract version: `v1`",
        "Plan contract version: `v1`",
        "`adaptation_contract_version`",
        "`assistant_feedback_adaptation`",
        "`adaptation_policy`",
        "`assistant_feedback_learning`",
        "`assistant_plan`",
        "`feedback_adaptation_policy_forced_fallback`",
        "`feedback_adaptation_latest_signal_not_allowlisted`",
        "`feedback_adaptation_boosted_intents_exceed_max`",
        "`feedback_adaptation_suppressed_intents_exceed_max`",
        "`feedback_adaptation_runtime_wired`",
        "`feedback_adaptation_runtime_backfilled`",
        "`feedback_adaptation_runtime_unknown_intent_removed`",
        "`feedback_adaptation_runtime_overlap_removed`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing feedback adaptation runtime marker: {marker}"


def test_feedback_adaptation_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/FEEDBACK_ADAPTATION_RUNTIME.md" in readme
    assert "Feedback adaptation runtime docs quality gate" in roadmap
