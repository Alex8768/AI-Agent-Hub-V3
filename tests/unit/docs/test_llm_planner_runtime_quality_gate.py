from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_llm_planner_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/LLM_PLANNER_RUNTIME.md")
    required_markers = [
        "LLM planner contract version: `v1`",
        "Plan contract version: `v1`",
        "`llm_planner_contract_version`",
        "`assistant_llm_planner`",
        "`llm_planner_policy`",
        "`assistant_plan`",
        "`llm_planner_policy_forced_fallback`",
        "`llm_planner_intent_not_allowlisted`",
        "`llm_plan_id_intent_mismatch`",
        "`llm_planner_runtime_wired`",
        "`llm_planner_runtime_plan_id_synced`",
        "`feature_reasoning_llm_enabled=false`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing llm planner runtime marker: {marker}"


def test_llm_planner_runtime_quality_gate_readme_and_roadmap_references():
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "docs/architecture/LLM_PLANNER_RUNTIME.md" in readme
    assert "LLM planner runtime docs quality gate" in roadmap
