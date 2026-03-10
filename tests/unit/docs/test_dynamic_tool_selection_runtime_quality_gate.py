from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dynamic_tool_selection_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/DYNAMIC_TOOL_SELECTION_RUNTIME.md")
    required_markers = [
        "Tool selection contract version: `v1`",
        "Plan contract version: `v1`",
        "`tool_selection_contract_version`",
        "`assistant_tool_selection`",
        "`tool_selection_policy`",
        "`assistant_plan`",
        "`tool_selection_policy_forced_fallback`",
        "`tool_selection_step_not_in_plan`",
        "`tool_selection_route_not_allowlisted`",
        "`tool_selection_runtime_wired`",
        "`tool_selection_runtime_backfilled`",
        "`tool_selection_runtime_orphaned_steps_removed`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing dynamic tool selection runtime marker: {marker}"


def test_dynamic_tool_selection_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/DYNAMIC_TOOL_SELECTION_RUNTIME.md" in readme
    assert "Dynamic tool selection runtime docs quality gate" in roadmap
