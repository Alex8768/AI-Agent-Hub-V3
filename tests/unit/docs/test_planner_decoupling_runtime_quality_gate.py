from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_planner_decoupling_runtime_quality_gate_architecture_doc_markers():
    content = _read("docs/architecture/PLANNER_DECOUPLING_RUNTIME.md")
    required_markers = [
        "`TD-A2.45-002`",
        "`decision_status: resolved_in_a2_48`",
        "`build_reasoning_planner_runtime`",
        "`normalize_reasoning_query_input`",
        "`planner_runtime_parity`",
        "`tests/unit/layers/pro/test_reasoning_kernel_runtime.py`",
        "`tests/unit/layers/pro/test_reasoning_planner.py`",
        "`tests/unit/layers/pro/test_reasoning_prompt_builder.py`",
        "`tests/unit/layers/pro/test_reasoning_engine_planner_runtime_parity.py`",
        "`tests/unit/docs/test_planner_decoupling_runtime_quality_gate.py`",
        "`feature_assistant_mode=false`",
        "`feature_assistant_proactive=false`",
        "`feature_assistant_actions=false`",
    ]
    for marker in required_markers:
        assert marker in content, f"Missing planner decoupling marker: {marker}"


def test_planner_decoupling_runtime_quality_gate_registry_and_references():
    registry = _read("docs/development/TECHNICAL_DEBT_REGISTRY.md")
    readme = _read("README.md")
    roadmap = _read("docs/roadmaps/pro-v3.1.md")

    assert "### debt_id: `TD-A2.45-002`" in registry
    assert "resolved_in_a2_48" in registry
    assert "docs/architecture/PLANNER_DECOUPLING_RUNTIME.md" in readme
    assert "Planner decoupling runtime docs quality gate" in roadmap

