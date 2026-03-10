from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_controlled_execution_pilot_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/CONTROLLED_EXECUTION_PILOT_RUNTIME.md")
    required_markers = [
        "Execution pilot contract version: `v1`",
        "Execution receipt contract version: `v1`",
        "`assistant_execution_pilot`",
        "`assistant_execution_receipt`",
        "`execution_transition_policy`",
        "`execution_pilot_contract_version`",
        "`allowlisted_action_types`",
        "`allowlisted_action_pattern`",
        "`rollback_contract_status`",
        "`rollback_missing_action_ids`",
        "`rollback_contract_missing_for_approved_actions`",
        "`executed_in_pilot`",
        "`pilot_runtime_execution_recorded`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing controlled execution pilot runtime marker: {marker}"


def test_controlled_execution_pilot_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/CONTROLLED_EXECUTION_PILOT_RUNTIME.md" in readme
    assert "Controlled execution pilot runtime docs quality gate" in roadmap
