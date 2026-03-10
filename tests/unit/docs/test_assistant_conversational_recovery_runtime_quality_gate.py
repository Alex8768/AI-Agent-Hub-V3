from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assistant_conversational_recovery_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/ASSISTANT_CONVERSATIONAL_RECOVERY_RUNTIME.md")
    required_markers = [
        "Assistant contract version: `v1`",
        "Plan contract version: `v1`",
        "`assistant_contract_version`",
        "`response_mode`",
        "`response_language`",
        "`assistant_recovery_policy`",
        "`assistant_chat_recovery_applied`",
        "`assistant_plan`",
        "`planning_reason_codes`",
        "`general_chat`",
        "`general_query`",
        "`assistant_chat_recovery_policy_forced_fallback`",
        "`assistant_chat_recovery_assistant_mode_disabled`",
        "`assistant_chat_recovery_requires_low_evidence`",
        "`assistant_chat_recovery_intent_not_allowlisted`",
        "`assistant_chat_recovery_greeting_blocked`",
        "`assistant_chat_recovery_language_not_allowlisted`",
        "`assistant_chat_recovery_runtime_wired`",
        "`assistant_chat_recovery_runtime_unknown_violation_removed`",
        "`assistant_chat_recovery_runtime_applied_flag_reset`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing assistant conversational recovery runtime marker: {marker}"


def test_assistant_conversational_recovery_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/ASSISTANT_CONVERSATIONAL_RECOVERY_RUNTIME.md" in readme
    assert "Conversational recovery runtime docs quality gate" in roadmap
