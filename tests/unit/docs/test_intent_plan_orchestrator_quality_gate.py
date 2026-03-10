from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_intent_plan_orchestrator_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/INTENT_PLAN_ORCHESTRATOR.md")
    required_markers = [
        "Intent contract version: `v1`",
        "Plan contract version: `v1`",
        "`assistant_intent`",
        "`assistant_plan`",
        "`planning_policy`",
        "`planning_reason_codes`",
        "`plan_id`",
        "`prepare_*_draft`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing intent-plan orchestrator marker: {marker}"


def test_intent_plan_orchestrator_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/INTENT_PLAN_ORCHESTRATOR.md" in readme
    assert "Intent-to-plan orchestrator docs quality gate" in roadmap
